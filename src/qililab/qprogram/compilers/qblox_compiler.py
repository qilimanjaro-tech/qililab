# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, cast

import numpy as np
import qpysequence as QPy
import qpysequence.program as QPyProgram
import qpysequence.program.instructions as QPyInstructions
from qprogram import BinaryOp, Constant, Range, Variable
from qprogram.blocks import Average, Block, Parallel, Sweep
from qprogram.operations import (
    Measure,
    Operation,
    ResetPhase,
    SetFrequency,
    SetGain,
    SetOffset,
    SetPhase,
    Sync,
    Wait,
)
from qprogram.operations import Play as CorePlay
from qprogram.waveforms import Arbitrary, FlatTop, IQWaveform, Square, Waveform
from qprogram_qblox import Acquire, Scope, SetMarkers, SetTrigger, WaitTrigger
from qpysequence.compiler import Compiler as QPyCompiler
from qpysequence.constants import INST_MAX_WAIT, INST_MIN_WAIT
from qpysequence.enums import TriggerCondition as QPyTriggerCondition

from qililab.config import logger
from qililab.constants import QBLOXCONSTANTS
from qililab.qprogram.blocks import IfTrigger, InfiniteLoop, for_loop_iterations
from qililab.qprogram.calibration import Calibration
from qililab.qprogram.compilers.prepass import prepare_qblox, prepare_shared
from qililab.qprogram.compilers.prepass.qblox_prepass import MAX_ACQUISITION_INDEX
from qililab.qprogram.crosstalk.crosstalk_matrix import CrosstalkMatrix
from qililab.qprogram.operations import MeasureReset, QbloxPlay
from qililab.qprogram.qprogram import QProgram

if TYPE_CHECKING:
    from qililab.pulse_distortion.pulse_distortion import PulseDistortion
    from qililab.qprogram.compilers.prepass.qblox_prepass import AcquisitionMetadata, ConditionalTrigger

# 2147483648 -> values >= this are "negative" in 2's complement (MSB = 1)
SIGN_BIT = 2**31
# 4294967293 == -3 in 2's complement
NEG_ONE_TO_THREE = (2**32) - 3

# TODO: move to qpysequence.constants
# 32 is the max number of acquisitions that can be stored

ENABLE_CONDITIONAL = 1
DISABLE_CONDITIONAL = 0

# time required by qblox trigger network to send a trigger; 400ns is conservative - the official guideline is 388ns between 2 modules
WAIT_TRIGGER_NETWORK_INTERMODULES = 400


def _trigger_address_mask(address: int) -> int:
    """``SetCond``/``Conditional`` mask bit for a trigger address (address=0 is a don't-care, no bit)."""
    return 0 if address == 0 else 2 ** (address - 1)


class _VariableExpression:
    """A variable plus or minus a constant or another variable, read as ``left operator right``.

    The Qblox pre-pass writes every expression this way: a constant only on the right, and never negative. Built by
    ``_compiled_value``.
    """

    def __init__(self, left: "Variable | int | float", operator: str, right: "Variable | int | float") -> None:
        self.left = left
        self.operator = operator
        self.right = right
        self.components = [left, right]
        self.variables = [component for component in self.components if isinstance(component, Variable)]
        self.constant = next((component for component in self.components if not isinstance(component, Variable)), None)

    def __repr__(self) -> str:
        return f"({self.left} {self.operator} {self.right})"


def _compiled_value(value: object) -> object:
    """Return a numeric operation argument as the compiler reads it: a ``Variable``, a number or a ``_VariableExpression``.

    The Qblox pre-pass leaves at most one ``+`` or ``-`` between a variable and a constant or another variable, a
    constant only on the right and never negative, and ``-x`` written ``0 - x``.

    Args:
        value (object): The argument, a number or a qprogram expression.

    Returns:
        object: The argument in the compiler's form.
    """
    if isinstance(value, Constant):
        return value.value
    if isinstance(value, BinaryOp):
        return _VariableExpression(_compiled_value(value.left), value.op, _compiled_value(value.right))  # type: ignore[arg-type]
    return value


def _waveforms_of(element: "CorePlay | QbloxPlay") -> tuple[Waveform, Waveform | None]:
    """Return the I and Q waveforms a play plays; Q is None for a single waveform.

    Args:
        element (CorePlay | QbloxPlay): The play.

    Returns:
        tuple[Waveform, Waveform | None]: The I and Q waveforms.
    """
    waveform = element.waveform
    if isinstance(waveform, IQWaveform):
        return waveform.get_I(), waveform.get_Q()
    return waveform, None  # type: ignore[return-value]


@dataclass
class AcquisitionData:
    """Class representing the output information generated by QbloxCompiler for an acquisition.

    Attributes:
        bus (str): The bus acquiring.
        shape (tuple): The number of points of each loop around the acquisitions, outermost first.
        intertwined (int): How many measurements write into the acquisition, one bin each in turn.
        measurements (list[str]): The names of those measurements, in the order their bins come.
        fields (list[tuple[str, ...]]): The fields each of those measurements returns.
        loops (list[Sweep | Parallel]): The loops around the acquisitions, outermost first, one per entry of ``shape``.
    """

    bus: str
    shape: tuple
    intertwined: int
    measurements: list[str] = field(default_factory=list)
    fields: list[tuple[str, ...]] = field(default_factory=list)
    loops: list[Sweep | Parallel] = field(default_factory=list)


Sequences = dict[str, QPy.Sequence]
Acquisitions = dict[str, dict[str, AcquisitionData]]


class QbloxCompilationOutput:
    """Class representing the output information generated by QbloxCompiler.

    Attributes:
        qprogram (QProgram): The compiled QProgram, with only the operations on Qblox buses.
        scopes (dict[str, Scope]): The ``qp.qblox.scope`` of each scoped bus.
        sequences (Sequence): A dictionary with the buses participating in the QProgram as keys and the corresponding Sequence as values.
        acquisitions (Acquisitions): A dictionary with the buses participating in the acquisitions as keys and the corresponding Acquisitions as values.
        requires_external_trigger (bool): Whether the compiled sequences wait on the cluster's external trigger, i.e. the
            QProgram has a ``wait_trigger`` on a Qblox bus or an ``if_trigger`` block.
        trigger_network_addresses (dict[str, int]): Buses that send their acquisition result on the trigger network,
            with their trigger address, i.e. the measurement buses of ``qp.qblox.measure_reset()``.
    """

    def __init__(
        self,
        qprogram: QProgram,
        sequences: Sequences,
        acquisitions: Acquisitions,
        requires_external_trigger: bool = False,
        trigger_network_addresses: dict[str, int] | None = None,
        scopes: dict[str, Scope] | None = None,
    ):
        self.qprogram = qprogram
        self.sequences = sequences
        self.acquisitions = acquisitions
        self.scopes = scopes if scopes is not None else {}
        self.requires_external_trigger = requires_external_trigger
        self.trigger_network_addresses = trigger_network_addresses if trigger_network_addresses is not None else {}

    def __iter__(self):
        """Allows the class to be unpacked as a tuple (program, config, measurements)."""
        yield self.sequences
        yield self.acquisitions


class BusCompilationInfo:
    """Class representing the information stored by QbloxCompiler for a bus."""

    def __init__(self) -> None:
        # The generated Sequence
        self.qpy_sequence = QPy.Sequence(
            program=QPy.Program(), waveforms=QPy.Waveforms(), acquisitions=QPy.Acquisitions(), weights=QPy.Weights()
        )
        self.acquisitions: dict[str, AcquisitionData] = {}

        # Dictionaries to hold mappings useful during compilation.
        self.variable_to_register: dict[Variable, QPyProgram.Register] = {}
        self.waveform_to_index: dict[str, int] = {}
        self.weight_to_index: dict[str, int] = {}
        self.acquisition_to_index: dict[str, int] = {}

        # Create and append the setup block to the Sequence's program
        setup_block = QPyProgram.Block(name="setup")
        self.qpy_sequence._program.add(setup_block)

        # Create and append the main block to the Sequence's program
        main_block = QPyProgram.Block(name="main")
        self.qpy_sequence._program.add(main_block)

        # Stacks to manage block hierarchy during compilation
        self.qpy_block_stack: deque[QPyProgram.Block] = deque([main_block])
        self.qprogram_block_stack: deque[Block] = deque()

        # Counters to help with naming and indexing
        self.loop_counter = 0
        self.average_counter = 0
        self.waveform_optimization_counter = 0

        # Syncing durations
        self.static_duration = 0
        self.dynamic_durations: list[Variable] = []
        self.sync_durations: list[QPyProgram.Register] = []
        self.duration_since_sync = 0
        self.dynamic_sync_counter: int = 0

        # Syncing marker. If true, a real-time instruction has been added since the last sync or the beginning of the program.
        self.marked_for_sync = False

        # Dynamic Syncing marker. If true, a dynamic variable has been used since the last sync or the beginning of the program.
        self.marked_for_dynamic_sync = False

        # Time of flight. Defaults to minimum_wait_duration and is updated if times_of_flight parameter is provided during compilation.
        self.time_of_flight = QbloxCompiler.minimum_wait_duration

        # Delay. Defaults 0 delay and is updated if delays parameter is provided within the runcard.
        self.delay = 0

        # Latched Parameter flag
        self.upd_param_instruction_pending: bool = False

        # Counters used for acquisition
        self.num_bins_per_acquire: int = 0
        self.num_bins_total: int = 0
        self.shape_acquire: tuple = ()
        self.bin_register: QPyProgram.Register = None

        # Allows reusing a register if a weight has already been given with the same value
        self.weight_index_to_register: dict[int, QPyProgram.Register] = {}

        # Registers values used for the hardware loop over time
        # (Target duration - this bus duration); negative/positive sign decides branching.
        self.delta_to_target_duration_register: QPyProgram.Register | None = None
        # Longest total (static + dynamic) duration among the other buses.
        self.max_other_total_duration_register: QPyProgram.Register | None = None
        # Longest static duration among the other buses.
        self.max_other_static_duration_register: QPyProgram.Register | None = None
        # (This bus's dynamic portion) + (dynamic bus's static duration).
        self.dynamic_plus_static_duration_register: QPyProgram.Register | None = None
        # Single wait chunk (to respect hardware limit on wait size).
        self.wait_chunk_duration_register: QPyProgram.Register | None = None

        # Variable Expression
        # Holds evaluated dynamic expression until consumed.
        self.dynamic_expression_register: QPyProgram.Register = None
        # True if the above value still needs to be applied to duration registers.
        self.has_pending_dynamic_expression: bool = False
        # Dynamic duration register for this bus.
        self.dynamic_duration_register: QPyProgram.Register | None = None

        # Count the number of different nested levels there are for this bus in a qprogram
        self.count_nested_level_acquire: int = -1

        # Count the number of acquire in one nested level
        self.counter_acquire: int = 0

        # Int of the previous nested level used
        self.prev_nested_level_acquire: int | None = None

        # Flag to know if an acquire is the first in a block
        self.first_acquire_of_block: bool = False

        # Used in instances where there are no loop on the bin
        self.single_bin_counter: int = 0

        # Bin index used in the move instruction
        self.start_bin_idx: int = 0

        # Flag used in _handle_acquire if acquisitions have more than 1 depth and the number of acquisitions exceeds MAX_ACQUISITION_INDEX
        self.exceeds_depth: bool = False


class QbloxCompiler:
    """A class for compiling QProgram to QBlox hardware."""

    minimum_wait_duration: int = 4

    def __init__(self) -> None:
        # Handlers to map each operation to a corresponding handler function
        self._handlers: dict[type, Callable] = {
            InfiniteLoop: self._handle_infinite_loop,
            Parallel: self._handle_parallel,
            Average: self._handle_average,
            Sweep: self._handle_sweep,
            SetFrequency: self._handle_set_frequency,
            SetPhase: self._handle_set_phase,
            ResetPhase: self._handle_reset_phase,
            SetGain: self._handle_set_gain,
            SetOffset: self._handle_set_offset,
            SetMarkers: self._handle_set_markers,
            SetTrigger: self._handle_set_trigger,
            Wait: self._handle_wait,
            WaitTrigger: self._handle_wait_trigger,
            Sync: self._handle_sync,
            Measure: self._handle_measure,
            MeasureReset: self._handle_measure_reset,
            Acquire: self._handle_acquire,
            Scope: self._handle_scope,
            CorePlay: self._handle_play,
            QbloxPlay: self._handle_play,
            IfTrigger: self._handle_block,
            Block: self._handle_block,
        }

        self._qprogram: QProgram
        self._buses: dict[str, BusCompilationInfo]
        self._sync_counter: int
        self._time_loop_counter: int = 0
        self._long_wait_dynamic: bool = False
        self._long_wait_dynamic_idx: int = 0
        self._max_wait_dynamic: int = 0
        self._markers: dict[str, str] | None
        self._disable_autosync: bool
        self._acquisition_metadata: AcquisitionMetadata = {}
        self._conditional: ConditionalTrigger | None = None
        self._single_channel: list[str] = []
        self._scopes: dict[str, Scope] = {}

    def compile(
        self,
        qprogram: QProgram,
        bus_mapping: dict[str, str] | None = None,
        calibration: Calibration | None = None,
        times_of_flight: dict[str, int] | None = None,
        delays: dict[str, int] | None = None,
        markers: dict[str, str] | None = None,
        qblox_buses: list[str] | None = None,
        single_channel: list[str] | None = None,
        bus_distortions: dict[str, list["PulseDistortion"]] | None = None,
        crosstalk: CrosstalkMatrix | None = None,
        readout_modules: dict[str, str] | None = None,
    ) -> QbloxCompilationOutput:
        """Compile QProgram to qpysequence.Sequence

        Args:
            qprogram (QProgram): The QProgram to be compiled
            bus_mapping (dict[str, str], optional): Optional mapping of bus names. Defaults to None.
            times_of_flight (dict[str, int], optional): Optional time of flight of bus. Defaults to None.
            readout_modules (dict[str, str], optional): The QRM of each bus that has one, used to check the program's
                ``qp.qblox.scope``. Defaults to None.

        Returns:
            QbloxCompilationOutput: Compiled sequences keyed by bus name, alongside acquisition
                metadata and measurement configurations.
        """

        def traverse(block: Block):
            delay_implemented = False
            for bus in self._buses:
                self._buses[bus].qprogram_block_stack.append(block)
                self._buses[bus].first_acquire_of_block = True
            for element in block.elements:
                if isinstance(element, (CorePlay, QbloxPlay)) and not delay_implemented:
                    for bus in self._buses:
                        if self._buses[bus].delay > 0:
                            self._handle_wait(element=Wait(bus=bus, duration=self._buses[bus].delay), delay=True)
                        elif self._buses[bus].delay < 0:
                            for other_buses in self._buses:
                                if other_buses != bus:
                                    self._handle_wait(
                                        element=Wait(bus=other_buses, duration=-self._buses[bus].delay), delay=True
                                    )
                    delay_implemented = True

                if (
                    isinstance(element, (Acquire, Measure, MeasureReset))
                    and element.bus in self._buses
                    and self._buses[element.bus].first_acquire_of_block is True
                ):
                    self._buses[element.bus].count_nested_level_acquire += 1
                    self._buses[element.bus].counter_acquire = self._acquisition_metadata[element.bus][id(block)][0]
                    self._buses[element.bus].first_acquire_of_block = False

                appended = self._handlers[type(element)](element)
                if isinstance(element, Block):
                    if isinstance(element, IfTrigger):
                        self._handle_conditional_trigger_prologue()
                    traverse(element)
                    if isinstance(element, IfTrigger):
                        self._handle_conditional_trigger_epilogue()
                    else:
                        # Conditional is deliberately excluded here: _handle_conditional_trigger_epilogue already
                        # pads the conditional bus to the exact expected_trigger_wait_time cadence, and
                        # the Qblox pre-pass guarantees no other instruction touches that bus
                        # outside the block -- an autosync here would stretch it to match unrelated buses and
                        # drift it out of phase with the QDAC's fixed trigger cadence on every iteration.
                        if not self._disable_autosync and isinstance(element, (Sweep, Parallel, Average)):
                            self._handle_sync(element=Sync(targets=None), delay=True)
                        if appended:
                            for bus in self._buses:
                                self._buses[bus].qpy_block_stack.pop()
            for bus in self._buses:
                self._buses[bus].qprogram_block_stack.pop()
                self._buses[bus].first_acquire_of_block = True

        prepass = prepare_qblox(
            prepare_shared(qprogram, bus_mapping=bus_mapping, calibration=calibration),
            calibration=calibration,
            crosstalk=crosstalk,
            bus_distortions=bus_distortions,
            qblox_buses=qblox_buses,
            readout_modules=readout_modules,
            markers=markers,
        )
        self._qprogram = prepass.qprogram
        self._disable_autosync = prepass.disable_autosync

        self._sync_counter = 0
        self._scopes = {}
        self._buses = self._populate_buses()
        self._single_channel = single_channel if single_channel is not None else []
        self._acquisition_metadata = prepass.acquisition_metadata
        self._conditional = prepass.conditional
        conditional_bus = self._conditional.bus if self._conditional is not None else None

        # Pre-processing: Update time of flight
        if times_of_flight is not None:
            for bus in self._buses.keys() & times_of_flight.keys():
                self._buses[bus].time_of_flight = times_of_flight[bus]

        # Pre-processing: Update delay
        if delays is not None:
            for bus in self._buses.keys() & delays.keys():
                self._buses[bus].delay = delays[bus]

        # Pre-processing: Set markers ON/OFF
        self._markers = markers
        for bus in self._buses:
            mask = self._markers[bus] if self._markers is not None and bus in self._markers else "0000"
            # if qprogram.measure_reset is used, the bus using the conditional enables latching at the very top of the q1asm
            self._buses[bus].qpy_sequence._program.blocks[0].add(QPyInstructions.WaitSync(4))
            if bus in prepass.latch_buses or bus == conditional_bus:
                self._buses[bus].qpy_sequence._program.blocks[0].add(QPyInstructions.SetLatchEn(1, 4), insert_idx=0)
            self._buses[bus].qpy_sequence._program.blocks[0].add(QPyInstructions.SetMrk(int(mask, 2)))
            self._buses[bus].qpy_sequence._program.blocks[0].add(QPyInstructions.UpdParam(4))
            if bus == conditional_bus:
                # Block once, here at the very end of setup (never inside main's loop), for the first
                # trigger pulse -- this is what phase-locks the sequencer to the QDAC's periodic cadence.
                # Every later check (once per if_trigger loop iteration) then only needs the non-blocking
                # SetCond/latch check in _handle_conditional_trigger_prologue/epilogue, relying on that
                # established cadence.
                self._buses[bus].qpy_sequence._program.blocks[0].add(
                    QPyInstructions.WaitTrigger(QBLOXCONSTANTS.EXT_TRIGGER_ADDRESS, INST_MIN_WAIT)
                )
            self._buses[bus].static_duration += 4

        for bus in prepass.exceeds_depth_buses:
            self._buses[bus].exceeds_depth = True

        traverse(self._qprogram._body)

        # Post-processing: Set all markers OFF, add stop instructions and compile
        for bus in self._buses:
            self._buses[bus].qpy_block_stack[0].add(component=QPyInstructions.SetMrk(0))
            self._buses[bus].qpy_block_stack[0].add(component=QPyInstructions.UpdParam(4))
            self._buses[bus].qpy_block_stack[0].add(component=QPyInstructions.Stop())

            if self._long_wait_dynamic:
                # TODO: this part of the q1asm can be simplified; using by creating a jump table using offset to only have one type of block per program

                if self._buses[bus].dynamic_durations:
                    for idx in range(self._long_wait_dynamic_idx):
                        self._buses[bus].qpy_block_stack[0].add(QPyProgram.Block(name=f"long_wait_{idx}"))
                        self._buses[bus].qpy_block_stack[0].add(component=QPyInstructions.Wait(INST_MAX_WAIT))
                        self._buses[bus].qpy_block_stack[0].add(
                            component=QPyInstructions.Sub(
                                self._buses[bus].wait_chunk_duration_register,
                                INST_MAX_WAIT,
                                self._buses[bus].wait_chunk_duration_register,
                            )
                        )
                        self._buses[bus].qpy_block_stack[0].add(
                            component=QPyInstructions.Jge(
                                self._buses[bus].wait_chunk_duration_register, INST_MAX_WAIT, f"long_wait_{idx}"
                            )
                        )
                        self._buses[bus].qpy_block_stack[0].add(
                            component=QPyInstructions.Wait(self._buses[bus].wait_chunk_duration_register)
                        )
                        self._buses[bus].qpy_block_stack[0].add(
                            component=QPyInstructions.Jmp(f"continue_after_long_wait_{idx}")
                        )

            # Check if variable waits are used to add the conditional labels after the stop in the q1asm
            if self._buses[bus].dynamic_sync_counter > 0:
                for idx in range(self._buses[bus].dynamic_sync_counter):
                    # Block to add the wait if needed following the Jlt instruction - the code goes into this block if the bus difference is positive
                    self._buses[bus].qpy_block_stack[0].add(QPyProgram.Block(name=f"dynamic_sync_{idx}"))
                    self._buses[bus].qpy_block_stack[0].add(
                        QPyInstructions.Jlt(
                            self._buses[bus].delta_to_target_duration_register, 1, f"after_dynamic_sync_{idx}"
                        )
                        # if the register difference is 0
                    )
                    self._buses[bus].qpy_block_stack[0].add(
                        QPyInstructions.Jlt(
                            self._buses[bus].delta_to_target_duration_register, INST_MIN_WAIT, f"one_two_three_{idx}"
                        )
                        # if the register difference is 1, 2 or 3
                    )
                    self._buses[bus].qpy_block_stack[0].add(
                        QPyInstructions.Jge(
                            self._buses[bus].delta_to_target_duration_register, INST_MAX_WAIT, f"long_wait_sync_{idx}"
                        )
                        # if long wait
                    )
                    self._buses[bus].qpy_block_stack[0].add(
                        component=QPyInstructions.Wait(self._buses[bus].delta_to_target_duration_register)
                    )
                    self._buses[bus].qpy_block_stack[0].add(component=QPyInstructions.Jmp(f"after_dynamic_sync_{idx}"))

                    #  Block to handle the case where the bus difference is 1, 2 or 3 - need to add the difference + 4 ns (the other buses will also add 4 ns)
                    self._buses[bus].qpy_block_stack[0].add(QPyProgram.Block(name=f"one_two_three_{idx}"))
                    self._buses[bus].qpy_block_stack[0].add(
                        component=QPyInstructions.Add(
                            self._buses[bus].delta_to_target_duration_register,
                            INST_MIN_WAIT,
                            self._buses[bus].delta_to_target_duration_register,
                        )
                    )
                    self._buses[bus].qpy_block_stack[0].add(
                        component=QPyInstructions.Wait(self._buses[bus].delta_to_target_duration_register)
                    )
                    self._buses[bus].qpy_block_stack[0].add(component=QPyInstructions.Jmp(f"after_dynamic_sync_{idx}"))

                    #  Block to handle the case where the bus difference is -1, -2 or -3 - need to add + 4 ns (the other buses will add 4 ns plus the integer)
                    self._buses[bus].qpy_block_stack[0].add(QPyProgram.Block(name=f"negative_one_two_three_{idx}"))
                    self._buses[bus].qpy_block_stack[0].add(component=QPyInstructions.Wait(4))
                    self._buses[bus].qpy_block_stack[0].add(component=QPyInstructions.Jmp(f"after_dynamic_sync_{idx}"))

                    # Block to handle wait above qblox limit
                    self._buses[bus].qpy_block_stack[0].add(QPyProgram.Block(name=f"long_wait_sync_{idx}"))
                    self._buses[bus].qpy_block_stack[0].add(component=QPyInstructions.Wait(INST_MAX_WAIT))
                    self._buses[bus].qpy_block_stack[0].add(
                        component=QPyInstructions.Sub(
                            self._buses[bus].delta_to_target_duration_register,
                            INST_MAX_WAIT,
                            self._buses[bus].delta_to_target_duration_register,
                        )
                    )
                    self._buses[bus].qpy_block_stack[0].add(
                        QPyInstructions.Jge(
                            self._buses[bus].delta_to_target_duration_register, INST_MAX_WAIT, f"long_wait_sync_{idx}"
                        )
                    )
                    self._buses[bus].qpy_block_stack[0].add(QPyInstructions.Jmp(f"dynamic_sync_{idx}"))

                    #  If the bus is static, an additional check must be implemented to find the longest other bus (dynamic/static comparison)
                    if self._buses[bus].max_other_total_duration_register is not None:
                        self._buses[bus].qpy_block_stack[0].add(QPyProgram.Block(name=f"other_max_duration_{idx}"))
                        self._buses[bus].qpy_block_stack[0].add(
                            component=QPyInstructions.Move(
                                self._buses[bus].max_other_static_duration_register,
                                self._buses[bus].max_other_total_duration_register,
                            )
                        )
                        self._buses[bus].qpy_block_stack[0].add(
                            component=QPyInstructions.Jmp(f"after_other_max_duration_{idx}")
                        )

            self._buses[bus].static_duration += 4
            compiler_qpysequence = QPyCompiler()
            self._buses[bus].qpy_sequence._program = compiler_qpysequence.compile(
                self._buses[bus].qpy_sequence._program, wait_sync=False
            )

        # Return a dictionary with bus names as keys and the compiled Sequence as values.
        sequences = {bus: bus_info.qpy_sequence for bus, bus_info in self._buses.items()}
        acquisitions = {bus: bus_info.acquisitions for bus, bus_info in self._buses.items()}
        return QbloxCompilationOutput(
            qprogram=self._qprogram,
            sequences=sequences,
            acquisitions=acquisitions,
            requires_external_trigger=prepass.requires_external_trigger,
            trigger_network_addresses=prepass.trigger_network_addresses,
            scopes=self._scopes,
        )

    def _populate_buses(self) -> dict[str, BusCompilationInfo]:
        """Map each bus in the QProgram, which only holds Qblox buses after the pre-pass, to a BusCompilationInfo instance.

        Returns:
            A dictionary where the keys are bus names and the values are BusCompilationInfo objects.
        """
        return {bus: BusCompilationInfo() for bus in self._qprogram.buses}

    def _append_to_waveforms_of_bus(
        self, bus: str, waveform_I: Waveform, waveform_Q: Waveform | None
    ) -> tuple[int, int, int]:
        """Append waveforms to Sequence's Waveforms of the given bus.

        Args:
            bus (str): Name of the bus.
            waveform_I (Waveform): I waveform.
            waveform_Q (Waveform | None): Q waveform.
        """

        def handle_waveform(waveform: Waveform | None, default_length: int = 0):
            _hash = QbloxCompiler._hash_waveform(waveform) if waveform else f"zeros {default_length}"

            if _hash in self._buses[bus].waveform_to_index:
                index = self._buses[bus].waveform_to_index[_hash]
                length = next(
                    len(waveform.data)
                    for waveform in self._buses[bus].qpy_sequence._waveforms._waveforms
                    if waveform.index == index
                )
                return index, length

            envelope = waveform.envelope() if waveform else np.zeros(default_length)
            index = self._buses[bus].qpy_sequence._waveforms.add(envelope)
            self._buses[bus].waveform_to_index[_hash] = index
            return index, len(envelope)

        index_I, length_I = handle_waveform(waveform_I, 0)
        if waveform_Q is None and bus in self._single_channel:
            index_Q, _ = handle_waveform(waveform_I, 0)
        else:
            index_Q, _ = handle_waveform(waveform_Q, len(waveform_I.envelope()))
        return index_I, index_Q, length_I

    def _append_to_weights_of_bus(self, bus: str, weights: IQWaveform) -> tuple[int, int, int]:
        def handle_weight(waveform: Waveform):
            _hash = QbloxCompiler._hash_waveform(waveform)

            if _hash in self._buses[bus].weight_to_index:
                index = self._buses[bus].weight_to_index[_hash]
                length = next(
                    len(weight.data)
                    for weight in self._buses[bus].qpy_sequence._weights._weights
                    if weight.index == index
                )
                return index, length

            envelope = waveform.envelope()
            length = len(envelope)
            index = self._buses[bus].qpy_sequence._weights.add(envelope)
            self._buses[bus].weight_to_index[_hash] = index
            return index, length

        index_I, length_I = handle_weight(weights.get_I())
        index_Q, _ = handle_weight(weights.get_Q())
        return index_I, index_Q, length_I

    def _handle_parallel(self, element: Parallel) -> bool:
        loops = []
        iterations = []
        for sweep in element.loops:
            source = cast("Range", sweep.source)
            loop_start, loop_stop = source.start, source.stop
            operation = QbloxCompiler._get_reference_operation_of_loop(loop=sweep, starting_block=element)
            qpysequence_operation = (
                QbloxCompiler._get_qpysequence_conversion_instructions(operation) if operation is not None else None
            )
            if isinstance(operation, Wait):
                if loop_start < INST_MIN_WAIT:
                    logger.warning(
                        f"Wait duration {loop_start} ns is below the Q1ASM minimum (4 ns), clamping to 4 ns."
                    )
                    loop_start = 4
                if loop_stop < INST_MIN_WAIT:
                    logger.warning(f"Wait duration {loop_stop} ns is below the Q1ASM minimum (4 ns), clamping to 4 ns.")
                    loop_stop = 4
            scale_factor = qpysequence_operation.scale_factor if qpysequence_operation is not None else None
            start, step, iters = QbloxCompiler._compute_loop_sweep(loop_start, loop_stop, source.step, scale_factor)
            loops.append((start, step, qpysequence_operation))
            iterations.append(iters)
        min_iterations = min(iterations)

        for bus in self._buses:
            qpy_loop = QPyProgram.IterativeLoop(
                name=f"loop_{self._buses[bus].loop_counter}", iterations=min_iterations, loops=loops
            )
            for i, sweep in enumerate(element.loops):
                self._buses[bus].variable_to_register[sweep.variable] = qpy_loop.loop_registers[i]
            self._buses[bus].qpy_block_stack[-1].add(qpy_loop)
            self._buses[bus].qpy_block_stack.append(qpy_loop)
            self._buses[bus].loop_counter += 1
        return True

    def _handle_average(self, element: Average) -> bool:
        for bus in self._buses:
            qpy_loop = QPyProgram.Loop(name=f"avg_{self._buses[bus].average_counter}", begin=element.shots)
            self._buses[bus].qpy_block_stack[-1].add(qpy_loop)
            self._buses[bus].qpy_block_stack.append(qpy_loop)
            self._buses[bus].average_counter += 1
        return True

    def _handle_infinite_loop(self, _: InfiniteLoop) -> bool:
        for bus in self._buses:
            qpy_loop = QPyProgram.InfiniteLoop(name=f"infinite_loop_{self._buses[bus].loop_counter}")
            self._buses[bus].qpy_block_stack[-1].add(qpy_loop)
            self._buses[bus].qpy_block_stack.append(qpy_loop)
            self._buses[bus].loop_counter += 1
        return True

    def _handle_sweep(self, sweep: Sweep) -> bool:
        source = cast("Range", sweep.source)
        loop_start, loop_stop = source.start, source.stop
        operation = QbloxCompiler._get_reference_operation_of_loop(sweep)
        qpysequence_operation = (
            QbloxCompiler._get_qpysequence_conversion_instructions(operation) if operation is not None else None
        )
        if isinstance(operation, Wait):
            if loop_start < INST_MIN_WAIT:
                logger.warning(f"Wait duration {loop_start} ns is below the Q1ASM minimum (4 ns), clamping to 4 ns.")
                loop_start = 4
            if loop_stop < INST_MIN_WAIT:
                logger.warning(f"Wait duration {loop_stop} ns is below the Q1ASM minimum (4 ns), clamping to 4 ns.")
                loop_stop = 4
        scale_factor = qpysequence_operation.scale_factor if qpysequence_operation is not None else None
        start, step, iterations = QbloxCompiler._compute_loop_sweep(loop_start, loop_stop, source.step, scale_factor)

        if isinstance(operation, Wait) and loop_stop > INST_MAX_WAIT:
            self._long_wait_dynamic = True
        self._max_wait_dynamic = int(loop_stop)

        for bus in self._buses:
            qpy_loop = QPyProgram.IterativeLoop(
                name=f"loop_{self._buses[bus].loop_counter}",
                iterations=iterations,
                loops=[(start, step, qpysequence_operation)],
            )
            self._buses[bus].qpy_block_stack[-1].add(qpy_loop)
            self._buses[bus].qpy_block_stack.append(qpy_loop)
            self._buses[bus].variable_to_register[sweep.variable] = qpy_loop.loop_registers[0]
            self._buses[bus].loop_counter += 1
        return True

    def _handle_set_frequency(self, element: SetFrequency) -> None:
        frequency = _compiled_value(element.frequency)
        if isinstance(frequency, Variable):
            freq = self._buses[element.bus].variable_to_register[frequency]
            instruction = QPyInstructions.SetFreq(value=freq)
        else:
            instruction = QPyInstructions.SetFrequencyHz(frequency_hz=frequency)

        self._buses[element.bus].qpy_block_stack[-1].add(component=instruction)

        self._buses[element.bus].upd_param_instruction_pending = True

    def _handle_set_phase(self, element: SetPhase) -> None:
        phase = _compiled_value(element.phase)
        if isinstance(phase, Variable):
            phase_register = self._buses[element.bus].variable_to_register[phase]
            instruction = QPyInstructions.SetPh(value=phase_register)
        else:
            instruction = QPyInstructions.SetPhaseRad(phase=phase)

        self._buses[element.bus].qpy_block_stack[-1].add(component=instruction)
        self._buses[element.bus].upd_param_instruction_pending = True

    def _handle_reset_phase(self, element: ResetPhase) -> None:
        self._buses[element.bus].qpy_block_stack[-1].add(component=QPyInstructions.ResetPh())
        self._buses[element.bus].upd_param_instruction_pending = True

    def _handle_latch_rst(self, bus: str, duration: int) -> None:
        self._buses[bus].qpy_block_stack[-1].add(component=QPyInstructions.LatchRst(duration=duration))
        self._buses[bus].marked_for_sync = True
        self._buses[bus].duration_since_sync += duration
        self._buses[bus].static_duration += duration

    def _resolve_binary_expression(
        self, bus: str, expression: _VariableExpression, convert: Callable
    ) -> QPyProgram.Register:
        """Emit Q1ASM instructions that evaluate a binary expression and return the result register.

        Emits: a leading Nop, then Add or Sub, then a trailing Nop to guard
        against a read-after-write hazard on the result register. The caller is
        responsible for emitting only the final parameter instruction
        (SetAwgGain, SetAwgOffs).

        Q1ASM forbids an immediate as the first operand of Add and Sub. For
        "+", ``_compiled_value`` guarantees the constant
        is always on the right, so Add(register, immediate, result) is always
        valid here. For "-", the left operand may be an immediate (e.g.
        ``cst - variable``), which is handled explicitly below.
        """
        # TODO: the flattening of all variable expressions will be moved to qpysequence

        left_component, right_component = expression.components
        left = (
            self._buses[bus].variable_to_register[left_component]
            if isinstance(left_component, Variable)
            else convert(left_component)
        )
        right = (
            self._buses[bus].variable_to_register[right_component]
            if isinstance(right_component, Variable)
            else convert(right_component)
        )
        result = QPyProgram.Register()

        if expression.operator == "+":
            self._buses[bus].qpy_block_stack[-1].add(component=QPyInstructions.Add(left, right, result))
        elif expression.operator == "-":
            if isinstance(left, QPyProgram.Register):
                self._buses[bus].qpy_block_stack[-1].add(component=QPyInstructions.Sub(left, right, result))
            # Q1ASM forbids the first element of sub to be an immediate
            else:
                constant_register = QPyProgram.Register()
                if left < 0:
                    loops = [
                        (i, loop)
                        for i, loop in enumerate(self._buses[bus].qpy_block_stack)
                        if isinstance(loop, QPyProgram.IterativeLoop) and not loop.name.startswith("avg")
                    ]
                    block_idx = loops[0][0] - 1 if loops else -2
                    zero_register = QPyProgram.Register()
                    self._buses[bus].qpy_block_stack[block_idx].add(
                        component=QPyInstructions.Move(source=0, destination=zero_register), insert_idx=0
                    )
                    self._buses[bus].qpy_block_stack[-1].add(
                        component=QPyInstructions.Sub(zero_register, abs(left), constant_register)
                    )
                else:
                    # TODO: this move is done at every loop iteration; ideally it belongs outside the loop
                    # where loop registers are initialised — requires a qpysequence change.
                    self._buses[bus].qpy_block_stack[-1].add(component=QPyInstructions.Move(left, constant_register))

                self._buses[bus].qpy_block_stack[-1].add(
                    component=QPyInstructions.Sub(constant_register, right, result)
                )

        return result

    def _handle_set_gain(self, element: SetGain) -> None:
        gain = _compiled_value(element.gain)
        if isinstance(gain, _VariableExpression):
            result = self._resolve_binary_expression(
                element.bus, gain, lambda x: int(x * QPyInstructions.SetNormalisedGain.scale_factor)
            )
            self._buses[element.bus].qpy_block_stack[-1].add(
                component=QPyInstructions.SetAwgGain(value_0=result, value_1=result)
            )
            self._buses[element.bus].upd_param_instruction_pending = True
            return
        if isinstance(gain, Variable):
            gain_register = self._buses[element.bus].variable_to_register[gain]
            instruction = QPyInstructions.SetAwgGain(value_0=gain_register, value_1=gain_register)
        else:
            instruction = QPyInstructions.SetNormalisedGain(gain_i=gain, gain_q=gain)

        self._buses[element.bus].qpy_block_stack[-1].add(component=instruction)
        self._buses[element.bus].upd_param_instruction_pending = True

    def _handle_set_offset(self, element: SetOffset) -> None:
        offset_path0 = _compiled_value(element.offset_path0)
        offset_path1 = _compiled_value(element.offset_path1)
        if isinstance(offset_path0, _VariableExpression):
            result = self._resolve_binary_expression(
                element.bus, offset_path0, lambda x: int(x * QPyInstructions.SetNormalisedOffs.scale_factor)
            )
            self._buses[element.bus].qpy_block_stack[-1].add(
                component=QPyInstructions.SetAwgOffs(value_0=result, value_1=result)
            )

        # TODO: the flattening of all variable expressions will be moved to qpysequence
        else:
            offset_0 = (
                self._buses[element.bus].variable_to_register[offset_path0]
                if isinstance(offset_path0, Variable)
                else offset_path0
            )
            if offset_path1 is None:
                offset_1 = offset_0
                logger.warning(
                    "Qblox requires an offset for the two paths, the offset of the second path has been set to the same as the first path."
                )

            else:
                offset_1 = (
                    self._buses[element.bus].variable_to_register[offset_path1]
                    if isinstance(offset_path1, Variable)
                    else offset_path1
                )

            if (isinstance(offset_0, QPyProgram.Register) and not isinstance(offset_1, QPyProgram.Register)) or (
                isinstance(offset_1, QPyProgram.Register) and not isinstance(offset_0, QPyProgram.Register)
            ):
                loops = [
                    (i, loop)
                    for i, loop in enumerate(self._buses[element.bus].qpy_block_stack)
                    if isinstance(loop, QPyProgram.IterativeLoop) and not loop.name.startswith("avg")
                ]
                block_index_for_move_instruction = loops[0][0] - 1 if loops else -2
                register = QPyProgram.Register()
                if isinstance(offset_0, QPyProgram.Register):
                    value = int(offset_1 * QPyInstructions.SetNormalisedOffs.scale_factor)
                    offset_1 = register
                else:
                    value = int(offset_0 * QPyInstructions.SetNormalisedOffs.scale_factor)
                    offset_0 = register

                self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction]._add_structure(
                    component=QPyInstructions.Move(source=abs(value), destination=register), insert_idx=0
                )
                if value < 0:
                    self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction]._add_structure(
                        component=QPyInstructions.Not(source=register, destination=register), insert_idx=1
                    )
                    self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction]._add_structure(
                        component=QPyInstructions.Add(a=register, b=1, destination=register), insert_idx=2
                    )

                self._buses[element.bus].qpy_block_stack[-1].add(
                    component=QPyInstructions.SetAwgOffs(value_0=offset_0, value_1=offset_1)
                )

            elif isinstance(offset_0, QPyProgram.Register) and isinstance(offset_1, QPyProgram.Register):
                self._buses[element.bus].qpy_block_stack[-1].add(
                    component=QPyInstructions.SetAwgOffs(value_0=offset_0, value_1=offset_1)
                )

            else:
                self._buses[element.bus].qpy_block_stack[-1].add(
                    component=QPyInstructions.SetNormalisedOffs(offset_i=offset_0, offset_q=offset_1)
                )

        self._buses[element.bus].upd_param_instruction_pending = True

    def _handle_set_markers(self, element: SetMarkers) -> None:
        marker_outputs = int(element.mask, 2)
        self._buses[element.bus].qpy_block_stack[-1].add(component=QPyInstructions.SetMrk(mask=marker_outputs))
        self._buses[element.bus].upd_param_instruction_pending = True

    def _handle_set_trigger(self, element: SetTrigger) -> None:
        mask = self._markers[element.bus] if self._markers is not None and element.bus in self._markers else "0000"
        # The Qblox pre-pass checks the outputs against the module
        output_map = {1: 3, 2: 2} if int(mask, 2) > 0 else {1: 3, 2: 2, 3: 1, 4: 0}
        outputs = cast("list[int] | int", element.outputs)
        for output in outputs if isinstance(outputs, list) else [outputs]:
            markers = list(mask)
            markers[output_map[output]] = "1"

        self._buses[element.bus].qpy_block_stack[-1].add(
            component=QPyInstructions.SetMrk(mask=int("".join(markers), 2))
        )
        self._buses[element.bus].upd_param_instruction_pending = True

        for bus in self._buses:
            self._handle_wait(element=Wait(bus=bus, duration=int(element.duration)), delay=True)

        self._buses[element.bus].qpy_block_stack[-1].add(component=QPyInstructions.SetMrk(mask=int(mask, 2)))
        self._buses[element.bus].upd_param_instruction_pending = True

    def _handle_wait(self, element: Wait, delay: bool = False) -> None:
        duration = _compiled_value(element.duration)
        if isinstance(duration, (Variable, _VariableExpression)):
            if self._buses[element.bus].marked_for_dynamic_sync is True:
                raise NotImplementedError(
                    "It is not currently not possible to have two dynamic wait without a sync in between them."
                )
            buses = set(self._buses)
            if not isinstance(duration, _VariableExpression):
                for bus in buses:
                    if self._buses[bus].dynamic_duration_register is None:
                        self._buses[bus].dynamic_duration_register = self._buses[bus].variable_to_register[duration]
                if duration not in self._buses[element.bus].dynamic_durations:
                    self._buses[element.bus].dynamic_durations.append(duration)

                if self._long_wait_dynamic:
                    for bus in buses:
                        if self._long_wait_dynamic_idx == 0:
                            self._buses[bus].wait_chunk_duration_register = QPyProgram.Register()

                        if self._buses[bus].dynamic_durations:
                            self._buses[bus].qpy_block_stack[-1].add(
                                component=QPyInstructions.Move(
                                    self._buses[bus].dynamic_duration_register,
                                    self._buses[bus].wait_chunk_duration_register,
                                )
                            )
                            self._buses[bus].qpy_block_stack[-1].add(
                                component=QPyInstructions.Jge(
                                    self._buses[bus].dynamic_duration_register,
                                    INST_MAX_WAIT,
                                    f"long_wait_{self._long_wait_dynamic_idx}",
                                )
                            )
                            self._buses[bus].qpy_block_stack[-1].add(
                                component=QPyInstructions.Wait(self._buses[bus].dynamic_duration_register)
                            )
                            self._buses[bus].qpy_block_stack[-1].add(
                                QPyProgram.Block(f"continue_after_long_wait_{self._long_wait_dynamic_idx}")
                            )

                    self._long_wait_dynamic_idx += 1

                else:
                    self._buses[element.bus].qpy_block_stack[-1].add(
                        component=QPyInstructions.Wait(duration=self._buses[element.bus].dynamic_duration_register)
                    )

            else:
                self._buses[element.bus].dynamic_expression_register = QPyProgram.Register()

                # Retrieve the variable instead of the whole expression
                variable_duration = duration.variables[0]
                variable_duration_register = self._buses[element.bus].variable_to_register[variable_duration]
                constant_duration = cast("int", duration.constant)
                if variable_duration not in self._buses[element.bus].dynamic_durations:
                    self._buses[element.bus].dynamic_durations.append(variable_duration)

                if duration.operator == "+":
                    self._buses[element.bus].qpy_block_stack[-1].add(
                        component=QPyInstructions.Add(
                            variable_duration_register,
                            constant_duration,
                            self._buses[element.bus].dynamic_expression_register,
                        )
                    )
                    self._max_wait_dynamic = self._max_wait_dynamic + constant_duration

                    if self._max_wait_dynamic > INST_MAX_WAIT:
                        # TODO: this can lead to redundancies, for example if you wait a long wait and then a short wait; the second is also treated as a long wait
                        self._long_wait_dynamic = True
                    else:
                        self._buses[element.bus].qpy_block_stack[-1].add(
                            component=QPyInstructions.Wait(self._buses[element.bus].dynamic_expression_register)
                        )

                elif duration.operator == "-":
                    # CST - Time
                    if isinstance(duration.right, Variable):
                        constant_duration_register = QPyProgram.Register()
                        self._buses[element.bus].qpy_block_stack[-1].add(
                            component=QPyInstructions.Move(constant_duration, constant_duration_register)
                        )
                        self._buses[element.bus].qpy_block_stack[-1].add(
                            component=QPyInstructions.Sub(
                                constant_duration_register,
                                variable_duration_register,
                                self._buses[element.bus].dynamic_expression_register,
                            )
                        )
                    # Time - CST
                    else:
                        self._buses[element.bus].qpy_block_stack[-1].add(
                            component=QPyInstructions.Sub(
                                variable_duration_register,
                                constant_duration,
                                self._buses[element.bus].dynamic_expression_register,
                            )
                        )
                    if not self._long_wait_dynamic:
                        self._buses[element.bus].qpy_block_stack[-1].add(
                            component=QPyInstructions.Wait(self._buses[element.bus].dynamic_expression_register)
                        )
                if self._long_wait_dynamic:
                    dynamic_long_duration_register = self._buses[element.bus].dynamic_expression_register
                    for bus in buses:
                        if self._long_wait_dynamic_idx == 0:
                            self._buses[bus].wait_chunk_duration_register = QPyProgram.Register()

                        if self._buses[bus].dynamic_durations:
                            self._buses[bus].qpy_block_stack[-1].add(
                                component=QPyInstructions.Move(
                                    dynamic_long_duration_register, self._buses[bus].wait_chunk_duration_register
                                )
                            )
                            self._buses[bus].qpy_block_stack[-1].add(
                                component=QPyInstructions.Jge(
                                    dynamic_long_duration_register,
                                    INST_MAX_WAIT,
                                    f"long_wait_{self._long_wait_dynamic_idx}",
                                )
                            )
                            self._buses[bus].qpy_block_stack[-1].add(
                                component=QPyInstructions.Wait(dynamic_long_duration_register)
                            )
                            self._buses[bus].qpy_block_stack[-1].add(
                                QPyProgram.Block(f"continue_after_long_wait_{self._long_wait_dynamic_idx}")
                            )

                    self._long_wait_dynamic_idx += 1

                # the other buses also need to replicate this operation to be tracking correctly for the dynamic syncs
                for bus in buses:
                    if bus != element.bus:
                        if self._buses[bus].dynamic_expression_register is None:
                            self._buses[bus].dynamic_expression_register = QPyProgram.Register()

                        variable_duration_register = self._buses[bus].variable_to_register[variable_duration]

                        if duration.operator == "+":
                            self._buses[bus].qpy_block_stack[-1].add(
                                component=QPyInstructions.Add(
                                    variable_duration_register,
                                    constant_duration,
                                    self._buses[bus].dynamic_expression_register,
                                )
                            )

                        elif duration.operator == "-":
                            # CST - Time
                            if isinstance(duration.right, Variable):
                                constant_duration_register = QPyProgram.Register()
                                self._buses[bus].qpy_block_stack[-1].add(
                                    component=QPyInstructions.Move(constant_duration, constant_duration_register)
                                )
                                self._buses[bus].qpy_block_stack[-1].add(
                                    component=QPyInstructions.Sub(
                                        constant_duration_register,
                                        variable_duration_register,
                                        self._buses[bus].dynamic_expression_register,
                                    )
                                )

                            # Time - CST
                            else:
                                self._buses[bus].qpy_block_stack[-1].add(
                                    component=QPyInstructions.Sub(
                                        variable_duration_register,
                                        constant_duration,
                                        self._buses[bus].dynamic_expression_register,
                                    )
                                )
                    self._buses[bus].has_pending_dynamic_expression = True

            self._buses[element.bus].marked_for_dynamic_sync = True
            self._time_loop_counter += 1

        else:
            static_duration = QbloxCompiler._clamp_duration(duration, label="wait")  # type: ignore[arg-type]
            if not delay:
                self._buses[element.bus].static_duration += static_duration
                self._buses[element.bus].duration_since_sync += static_duration
            # loop over wait instructions if static duration is longer than allowed qblox max wait time of 2**16 -4
            self._handle_add_waits(bus=element.bus, duration=static_duration)

        self._buses[element.bus].marked_for_sync = True

    @staticmethod
    def _clamp_duration(duration: int, label: str = "duration") -> int:
        """Clamp to INST_MIN_WAIT if below INST_MIN_WAIT.
        The returned duration is rounded.

        Args:
            duration: The requested duration in ns.
            label: Name used in warning messages to identify the instruction.

        Returns:
            The given duration rounded, clamped to INST_MIN_WAIT if below INST_MIN_WAIT.
        """
        if duration < INST_MIN_WAIT:
            logger.warning(
                f"{label} duration {duration} ns is below the Q1ASM minimum ({INST_MIN_WAIT} ns), clamping to {INST_MIN_WAIT} ns."
            )
            return INST_MIN_WAIT
        return int(duration)

    def _handle_add_waits(self, bus: str, duration: int) -> None:
        """Emit wait instructions for the given bus, handling durations longer than INST_MAX_WAIT
        via ``LongWait`` and flushing any pending ``upd_param`` before the wait.

        Args:
            bus (str): Bus identifier.
            duration (int): Duration to wait in ns.
        """
        if self._buses[bus].upd_param_instruction_pending:
            if duration <= INST_MAX_WAIT:
                self._buses[bus].qpy_block_stack[-1].add(component=QPyInstructions.UpdParam(duration=duration))
            else:
                self._buses[bus].qpy_block_stack[-1].add(
                    component=QPyInstructions.LongWait(duration=duration, upd_param=True)
                )

            self._buses[bus].upd_param_instruction_pending = False

        # no instructions pending
        else:
            if duration <= INST_MAX_WAIT:
                self._buses[bus].qpy_block_stack[-1].add(component=QPyInstructions.Wait(duration=duration))
            else:
                self._buses[bus].qpy_block_stack[-1].add(component=QPyInstructions.LongWait(duration=duration))

    def _handle_wait_trigger(self, element: WaitTrigger) -> None:
        """Emit a wait for an external trigger on every Qblox bus in the QProgram.

        Buses are synced (including delay compensation) before the trigger wait, then each bus
        receives its own wait_trigger instruction for the same duration, keeping them synchronized
        without a separate wait_sync.

        Args:
            element (WaitTrigger): The wait_trigger element to compile.
        """
        # The Qblox pre-pass refuses a variable duration
        duration = QbloxCompiler._clamp_duration(cast("int", element.duration), label="wait_trigger")

        # Flush any pending upd_param before the sync, so every bus reaches the trigger aligned and
        # waits on it with the same plain wait_trigger.
        for bus in self._buses:
            if self._buses[bus].upd_param_instruction_pending:
                self._buses[bus].qpy_block_stack[-1].add(component=QPyInstructions.UpdParam(duration=INST_MIN_WAIT))
                self._buses[bus].static_duration += INST_MIN_WAIT
                self._buses[bus].duration_since_sync += INST_MIN_WAIT
                self._buses[bus].upd_param_instruction_pending = False
                self._buses[bus].marked_for_sync = True

        self._handle_sync(element=Sync(targets=None), delay=True)

        if element.port is not None:
            logger.warning(
                "wait_trigger port is ignored on Qblox buses: the wait always uses the cluster's external "
                "trigger address. The port argument only applies to QDACII buses."
            )
        for bus in self._buses:
            self._handle_add_trigger_waits(bus=bus, duration=duration, port=QBLOXCONSTANTS.EXT_TRIGGER_ADDRESS)

        # All buses received an identical duration above, so they remain balanced; just clear sync bookkeeping.
        for bus in self._buses:
            self._buses[bus].marked_for_sync = False
            self._buses[bus].duration_since_sync = 0

    def _handle_add_trigger_waits(self, bus: str, duration: int, port: int) -> None:
        """Emit a wait-trigger instruction for the given bus, handling durations longer than
        INST_MAX_WAIT.

        Args:
            bus (str): Bus identifier.
            duration (int): Duration to wait in ns.
            port (int): Trigger network address to wait on.
        """
        if duration <= INST_MAX_WAIT:
            self._buses[bus].qpy_block_stack[-1].add(
                component=QPyInstructions.WaitTrigger(trigger=port, duration=duration)
            )
        else:
            self._buses[bus].qpy_block_stack[-1].add(
                component=QPyInstructions.LongWaitTrigger(trig_addr=port, duration=duration)
            )
        self._buses[bus].static_duration += duration
        self._buses[bus].duration_since_sync += duration
        self._buses[bus].marked_for_sync = True

    def _handle_sync(self, element: Sync, delay: bool = False) -> None:
        # Get the buses involved in the sync operation.
        buses = set(element.targets or self._buses)

        # If they are zero or one, return.
        if len(buses) <= 1:
            return

        # If there is no bus marked for sync, return.
        if all(not self._buses[bus].marked_for_sync and not self._buses[bus].marked_for_dynamic_sync for bus in buses):
            return

        # Is there any bus that has dynamic durations?
        if any(self._buses[bus].marked_for_dynamic_sync for bus in buses):
            self._handle_dynamic_sync(buses=buses, include_delay=delay)
        else:
            # If no, calculating the difference is trivial.
            self._handle_static_sync(buses=buses, include_delay=delay)

        # In any case, mark all buses as synced.
        for bus in buses:
            self._buses[bus].marked_for_sync = False
            self._buses[bus].marked_for_dynamic_sync = False
            self._buses[bus].duration_since_sync = 0

    def _handle_static_sync(self, buses: set[str], include_delay: bool = False) -> None:
        """
        Equalize durations across buses when there are no dynamic waits pending. If self._time_loop_counter == 0, we equalize on `static_duration`.
        Otherwise, we equalize on `duration_since_sync`.
        If include_delay is True, we also align each bus's delay so the  total (duration + delay) is matched.
        """
        duration_attr = "static_duration" if self._time_loop_counter == 0 else "duration_since_sync"
        max_duration = max(getattr(self._buses[bus], duration_attr) for bus in buses)
        max_delay = max(self._buses[bus].delay for bus in buses) if include_delay else 0
        for bus in buses:
            current_duration = getattr(self._buses[bus], duration_attr)
            delay_diff = (max_delay - self._buses[bus].delay) if include_delay else 0
            duration_diff = (max_duration - current_duration) + delay_diff
            if duration_diff > 0:
                self._handle_add_waits(bus=bus, duration=duration_diff)
                # Only update static_duration once; if duration_attr == duration_since_sync, do not
                # increment static_duration (it represents total compiled time).
                if duration_attr == "static_duration":
                    self._buses[bus].static_duration += duration_diff
                else:
                    for (
                        non_synced_bus
                        # Add a negative penalty for a bus that was not synced with the others
                    ) in self._buses:
                        if non_synced_bus not in buses:
                            self._buses[non_synced_bus].duration_since_sync += -max_duration
                    self._buses[bus].duration_since_sync += duration_diff

    def _handle_dynamic_sync(self, buses: set[str], include_delay: bool = False) -> None:
        #  TODO: Implement the case where two buses use the time variable - this will require an additional check similar to the one currently done between the maximum time of the other buses (now we ocmpare the max static and the dynamic,
        #  but when two buses will be dynamic we need to find the max dynamic before the max static/dynamic)
        #  TODO using two times a variable wait is ok but a sync between them is required for now
        # Add delay if needed
        for bus in buses:
            if (
                self._buses[bus].duration_since_sync < 0
                # If a penalty has been added in static sync, handle it as a standalone wait
            ):
                self._buses[bus].qpy_block_stack[-1].add(
                    QPyInstructions.Wait(abs(self._buses[bus].duration_since_sync))
                )
                self._buses[bus].duration_since_sync = 0
            max_delay = max(self._buses[bus].delay for bus in buses) if include_delay else 0
            delay_diff = (max_delay - self._buses[bus].delay) if include_delay else 0
            if delay_diff > 0:
                self._handle_add_waits(bus=bus, duration=delay_diff)
                self._buses[bus].duration_since_sync += delay_diff

        # Find the dynamic bus
        count_dynamic_bus = 0
        for bus in buses:
            if self._buses[bus].dynamic_durations:
                dynamic_bus = bus
                count_dynamic_bus += 1
                if count_dynamic_bus >= 2:
                    raise NotImplementedError(
                        "More than 2 buses have a dynamic duration, which is not yet implemented."
                    )

        for bus in buses:
            if self._buses[bus].dynamic_sync_counter == 0:
                self._buses[bus].max_other_static_duration_register = QPyProgram.Register()
                self._buses[bus].dynamic_plus_static_duration_register = QPyProgram.Register()
                self._buses[bus].delta_to_target_duration_register = QPyProgram.Register()
                if not self._buses[bus].dynamic_durations:
                    self._buses[bus].max_other_total_duration_register = QPyProgram.Register()

            #  Get the max static duration of the other buses
            max_bus = max(
                (bus_other for bus_other in buses if bus_other != bus),
                key=lambda bus_other: self._buses[bus_other].duration_since_sync,
            )
            max_static = self._buses[max_bus].duration_since_sync
            self._buses[bus].qpy_block_stack[-1].add(
                QPyInstructions.Move(max_static, self._buses[bus].max_other_static_duration_register)
            )

            # Compute the duration of the dynamic bus
            static_duration_dynamic_bus = self._buses[dynamic_bus].duration_since_sync

            if self._buses[bus].dynamic_durations:
                # TODO if the dynamic bus has the longest static duration, Q1ASM can be further simplified, no need for any comparison
                # TODO the Q1ASM can be simplified by checking if the static duration is 0 before using it
                if self._buses[bus].has_pending_dynamic_expression:
                    self._buses[bus].qpy_block_stack[-1].add(
                        QPyInstructions.Add(
                            self._buses[bus].dynamic_expression_register,
                            static_duration_dynamic_bus,
                            self._buses[bus].dynamic_plus_static_duration_register,
                        )
                    )
                    self._buses[bus].has_pending_dynamic_expression = False

                else:
                    self._buses[bus].qpy_block_stack[-1].add(
                        QPyInstructions.Add(
                            self._buses[bus].dynamic_duration_register,
                            static_duration_dynamic_bus,
                            self._buses[bus].dynamic_plus_static_duration_register,
                        )
                    )

                # Maximum duration of the other buses - Duration of this bus
                self._buses[bus].qpy_block_stack[-1].add(
                    QPyInstructions.Sub(
                        self._buses[bus].max_other_static_duration_register,
                        self._buses[bus].dynamic_plus_static_duration_register,
                        self._buses[bus].delta_to_target_duration_register,
                    )
                )

                # Check the sign of the bus difference, this is done comparing with 147483648 (2**31), anything above it is negative in two's complement (MSB is 1)
                # NEG_ONE_TO_THREE (4294967293) is -3 in two's complement
                self._buses[bus].qpy_block_stack[-1].add(
                    QPyInstructions.Jlt(
                        self._buses[bus].delta_to_target_duration_register,
                        SIGN_BIT,
                        f"dynamic_sync_{self._buses[bus].dynamic_sync_counter}",
                    )
                )
                self._buses[bus].qpy_block_stack[-1].add(
                    QPyInstructions.Jge(
                        self._buses[bus].delta_to_target_duration_register,
                        NEG_ONE_TO_THREE,
                        f"negative_one_two_three_{self._buses[bus].dynamic_sync_counter}",
                    )
                    # Check if the difference is -1, -2 or -3
                )

            else:
                current_bus_duration_register = QPyProgram.Register()

                if self._buses[bus].has_pending_dynamic_expression:
                    self._buses[bus].qpy_block_stack[-1].add(
                        QPyInstructions.Add(
                            self._buses[bus].dynamic_expression_register,
                            static_duration_dynamic_bus,
                            self._buses[bus].dynamic_plus_static_duration_register,
                        )
                    )
                    self._buses[bus].has_pending_dynamic_expression = False

                else:
                    self._buses[bus].qpy_block_stack[-1].add(
                        QPyInstructions.Add(
                            self._buses[bus].dynamic_duration_register,
                            static_duration_dynamic_bus,
                            self._buses[bus].dynamic_plus_static_duration_register,
                        )
                    )

                # Check which of the other buses has the longest duration (this check is needed in the Q1ASM as at least one bus will have dynamic duration)
                self._buses[bus].qpy_block_stack[-1].add(
                    QPyInstructions.Sub(
                        self._buses[bus].max_other_static_duration_register,
                        self._buses[bus].dynamic_plus_static_duration_register,
                        self._buses[bus].max_other_total_duration_register,
                    )
                )
                self._buses[bus].qpy_block_stack[-1].add(
                    QPyInstructions.Jlt(
                        self._buses[bus].max_other_total_duration_register,
                        SIGN_BIT,
                        f"other_max_duration_{self._buses[bus].dynamic_sync_counter}",
                    )
                )

                # If the Jlt condition is not met, the dynamic bus has the longest duration of the other bus
                self._buses[bus].qpy_block_stack[-1].add(
                    QPyInstructions.Move(
                        self._buses[bus].dynamic_plus_static_duration_register,
                        self._buses[bus].max_other_total_duration_register,
                    )
                )

                #  Add the block to label to continue after the comparison
                self._buses[bus].qpy_block_stack[-1].add(
                    QPyProgram.Block(name=f"after_other_max_duration_{self._buses[bus].dynamic_sync_counter}")
                )

                #  Move the static duration of the current bus to a register
                static_duration_current_bus = self._buses[bus].duration_since_sync
                self._buses[bus].qpy_block_stack[-1].add(
                    QPyInstructions.Move(static_duration_current_bus, current_bus_duration_register)
                )

                # This part is the same for the dynamic bus
                # Maximum duration of the other buses - Duration of this bus
                self._buses[bus].qpy_block_stack[-1].add(
                    QPyInstructions.Sub(
                        self._buses[bus].max_other_total_duration_register,
                        current_bus_duration_register,
                        self._buses[bus].delta_to_target_duration_register,
                    )
                )

                # Check the sign of the bus difference, this is done comparing with SIGN_BIT (2**31), anything above it is negative in two's complement (MSB is 1)
                # NEG_ONE_TO_THREE (4294967293) is -3 in two's complement
                self._buses[bus].qpy_block_stack[-1].add(
                    QPyInstructions.Jlt(
                        self._buses[bus].delta_to_target_duration_register,
                        SIGN_BIT,
                        f"dynamic_sync_{self._buses[bus].dynamic_sync_counter}",
                    )
                )
                self._buses[bus].qpy_block_stack[-1].add(
                    QPyInstructions.Jge(
                        self._buses[bus].delta_to_target_duration_register,
                        NEG_ONE_TO_THREE,
                        f"negative_one_two_three_{self._buses[bus].dynamic_sync_counter}",
                    )
                    # Check if the difference is -1, -2 or -3
                )

            # Add the block to label to continue after the comparison
            self._buses[bus].qpy_block_stack[-1].add(
                QPyProgram.Block(name=f"after_dynamic_sync_{self._buses[bus].dynamic_sync_counter}")
            )

            self._buses[bus].dynamic_sync_counter += 1

    def _handle_measure(self, element: Measure) -> None:
        """Compile a ``measure``: the play of its readout waveform and its acquisition, as one operation.

        Args:
            element (Measure): measure operation
        """
        time_of_flight = self._buses[element.bus].time_of_flight
        play = QbloxPlay(bus=element.bus, waveform=element.waveform, wait_time=time_of_flight)
        self._handle_play(play)
        self._handle_acquire(element)

    def _handle_scope(self, element: Scope) -> None:
        """Record the bus's ``qp.qblox.scope``: it configures the QRM's scope, and adds no instruction.

        Args:
            element (Scope): The scope operation.
        """
        self._scopes[element.bus] = element

    def _handle_acquire(self, element: "Acquire | Measure | MeasureReset") -> None:
        """Compile an ``Acquire`` operation to Q1ASM.

        Dispatches to ``_handle_acquire_exceeds_depth`` when the bus has more distinct
        acquisition blocks than the hardware can index (``exceeds_depth=True``), or to
        ``_handle_acquire_per_depth`` otherwise. The shared tail (duration tracking,
        sync markers) is applied after both paths.
        """
        # TODO: unify with measure when time of flight is implemented
        # The shared pre-pass resolves every calibrated weight name
        weights = cast("IQWaveform", element.weights)
        index_I, index_Q, integration_length = self._append_to_weights_of_bus(element.bus, weights)
        if self._buses[element.bus].exceeds_depth:
            self._handle_acquire_exceeds_depth(element, index_I, index_Q, integration_length)
        else:
            self._handle_acquire_per_depth(element, index_I, index_Q, integration_length)
        self._buses[element.bus].prev_nested_level_acquire = self._buses[element.bus].count_nested_level_acquire
        self._buses[element.bus].static_duration += integration_length
        self._buses[element.bus].duration_since_sync += integration_length
        self._buses[element.bus].marked_for_sync = True
        self._buses[element.bus].upd_param_instruction_pending = False

    def _handle_acquire_exceeds_depth(
        self, element: "Acquire | Measure | MeasureReset", index_I: int, index_Q: int, integration_length: int
    ) -> None:
        """Compile an ``Acquire`` when exceeds_depth is True.

        All acquisitions on this bus are collapsed into acquisition index 0. On the first
        call, a single bin register is initialised to 0 and the full bin count is
        registered. Every call emits one ``acquire_weighed`` into the current average
        block and one ``add`` into the outer block, so the bin pointer advances by 1
        after each average block completes.

        Only ``average`` blocks are supported in this path. If the block stack contains
        a ``for_loop`` (``QPyProgram.IterativeLoop``), a ``NotImplementedError`` is raised.

        Args:
            element: The acquire operation being compiled.
            index_I: Weight waveform index for the I path.
            index_Q: Weight waveform index for the Q path.
            integration_length: Integration window duration in nanoseconds.

        Raises:
            NotImplementedError: If a ``for_loop`` is present in the block stack.
        """
        if any(isinstance(loop, QPyProgram.IterativeLoop) for loop in self._buses[element.bus].qpy_block_stack):
            raise NotImplementedError(
                f"Bus '{element.bus}' has more than {MAX_ACQUISITION_INDEX + 1} acquisitions across separate blocks "
                f"and contains a 'for_loop'. Only 'average' blocks are supported in this case."
            )

        block_index_for_move_instruction = -2

        # Only for the first acquisition.
        if not self._buses[element.bus].acquisitions:
            num_acquisitions = len(self._acquisition_metadata[element.bus])
            acquisition_name = f"Acquisition {self._buses[element.bus].count_nested_level_acquire}"
            self._buses[element.bus].acquisitions[acquisition_name] = AcquisitionData(
                bus=element.bus,
                shape=(),
                intertwined=num_acquisitions,
            )
            self._buses[element.bus].qpy_sequence._acquisitions.add(
                name=acquisition_name,
                num_bins=num_acquisitions,
                index=self._buses[element.bus].count_nested_level_acquire,
            )
            self._buses[element.bus].bin_register = QPyProgram.Register()
            self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].add(
                component=QPyInstructions.Move(source=0, destination=self._buses[element.bus].bin_register),
                insert_idx=0,
            )

        acquisition_data = next(iter(self._buses[element.bus].acquisitions.values()))
        acquisition_data.measurements.append(element.name)
        acquisition_data.fields.append(element.fields)
        register_I = self._get_or_create_weight_register(element.bus, index_I, block_index_for_move_instruction)
        register_Q = self._get_or_create_weight_register(element.bus, index_Q, block_index_for_move_instruction)
        self._buses[element.bus].qpy_block_stack[-1].add(
            component=QPyInstructions.AcquireWeighed(
                acquisition=0,
                bin=self._buses[element.bus].bin_register,
                weight_0=register_I,
                weight_1=register_Q,
                duration=integration_length,
            )
        )
        self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].add(
            component=QPyInstructions.Add(
                a=self._buses[element.bus].bin_register,
                b=1,
                destination=self._buses[element.bus].bin_register,
            )
        )

    def _handle_acquire_per_depth(
        self, element: "Acquire | Measure | MeasureReset", index_I: int, index_Q: int, integration_length: int
    ) -> None:
        """Compile an ``Acquire`` in the standard case where each distinct nesting depth
        maps to its own acquisition index (index = ``count_nested_level_acquire``).

        On the first acquire at a new depth level the index is registered and, if the
        program contains iterative loops, a bin register is created and initialised.
        Sequential acquires inside the same average block each get their own register
        offset so consecutive bins are written in order. Single-bin acquires (no outer
        loops) use a literal bin index via ``single_bin_counter``.

        Args:
            element: The acquire operation being compiled.
            index_I: Weight waveform index for the I path.
            index_Q: Weight waveform index for the Q path.
            integration_length: Integration window duration in nanoseconds.
        """
        loops = [
            (i, loop)
            for i, loop in enumerate(self._buses[element.bus].qpy_block_stack)
            if isinstance(loop, QPyProgram.IterativeLoop) and not loop.name.startswith("avg")
        ]
        block_index_for_add_instruction = loops[-1][0] if loops else -1
        block_index_for_move_instruction = loops[0][0] - 1 if loops else -2

        # True when the innermost active block is an average loop.
        in_avg_block = isinstance(self._buses[element.bus].qpy_block_stack[-1], QPyProgram.Loop)
        is_avg_multi_acquire = in_avg_block and self._buses[element.bus].counter_acquire > 1

        # If it is the first acquire at this nested level, set everything up.
        if self._buses[element.bus].count_nested_level_acquire != self._buses[element.bus].prev_nested_level_acquire:
            self._buses[element.bus].start_bin_idx = 0
            self._buses[element.bus].shape_acquire = tuple(loop[1].iterations for loop in loops)
            self._buses[element.bus].num_bins_per_acquire = math.prod(loop[1].iterations for loop in loops)

            # total nb of bins is number of acquire x numbers of bins by acquire (for each nested level)
            self._buses[element.bus].num_bins_total = int(
                self._buses[element.bus].counter_acquire * self._buses[element.bus].num_bins_per_acquire
            )

            acquisition_name = f"Acquisition {self._buses[element.bus].count_nested_level_acquire}"
            self._buses[element.bus].acquisitions[acquisition_name] = AcquisitionData(
                bus=element.bus,
                shape=self._buses[element.bus].shape_acquire,
                intertwined=self._buses[element.bus].counter_acquire,
                loops=[
                    block
                    for block in self._buses[element.bus].qprogram_block_stack
                    if isinstance(block, (Sweep, Parallel))
                ],
            )
            self._buses[element.bus].qpy_sequence._acquisitions.add(
                name=acquisition_name,
                num_bins=self._buses[element.bus].num_bins_total,
                index=self._buses[element.bus].count_nested_level_acquire,
            )

            # using registers is required if the bins are greater than 1
            if self._buses[element.bus].num_bins_per_acquire > 1:
                self._buses[element.bus].bin_register = QPyProgram.Register()
                self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction].add(
                    component=QPyInstructions.Move(source=0, destination=self._buses[element.bus].bin_register),
                    insert_idx=0,
                )
                self._buses[element.bus].start_bin_idx += 1

        elif is_avg_multi_acquire and self._buses[element.bus].num_bins_per_acquire > 1:
            # Each sequential acquire directly inside an average block gets its own register, initialised
            # to the start_bin_idx so that consecutive acquires write to consecutive bins.
            # The register is never modified inside the average, it is modified in the add outside the average.
            self._buses[element.bus].bin_register = QPyProgram.Register()
            self._buses[element.bus].qpy_block_stack[block_index_for_move_instruction]._add_structure(
                component=QPyInstructions.Move(
                    source=self._buses[element.bus].start_bin_idx, destination=self._buses[element.bus].bin_register
                ),
                insert_idx=0,
            )
            self._buses[element.bus].start_bin_idx += 1

        acquisition_data = self._buses[element.bus].acquisitions[
            f"Acquisition {self._buses[element.bus].count_nested_level_acquire}"
        ]
        acquisition_data.measurements.append(element.name)
        acquisition_data.fields.append(element.fields)

        if self._buses[element.bus].num_bins_per_acquire > 1:
            register_I = self._get_or_create_weight_register(element.bus, index_I, block_index_for_move_instruction)
            register_Q = self._get_or_create_weight_register(element.bus, index_Q, block_index_for_move_instruction)
            self._buses[element.bus].qpy_block_stack[-1].add(
                component=QPyInstructions.AcquireWeighed(
                    acquisition=self._buses[element.bus].count_nested_level_acquire,
                    bin=self._buses[element.bus].bin_register,
                    weight_0=register_I,
                    weight_1=register_Q,
                    duration=integration_length,
                )
            )
            # Advance by N bins per step, where N is the number of acquires sharing this avg block.
            bins_per_step = self._buses[element.bus].counter_acquire if is_avg_multi_acquire else 1
            self._buses[element.bus].qpy_block_stack[block_index_for_add_instruction].add(
                component=QPyInstructions.Add(
                    a=self._buses[element.bus].bin_register,
                    b=bins_per_step,
                    destination=self._buses[element.bus].bin_register,
                )
            )
        # if only 1 bin, the use of register can be avoided
        else:
            if (
                self._buses[element.bus].prev_nested_level_acquire
                != self._buses[element.bus].count_nested_level_acquire
                # reset the bin index if new depth level
            ):
                self._buses[element.bus].single_bin_counter = 0
            self._buses[element.bus].qpy_block_stack[-1].add(
                component=QPyInstructions.AcquireWeighed(
                    acquisition=self._buses[element.bus].count_nested_level_acquire,
                    bin=self._buses[element.bus].single_bin_counter,
                    weight_0=index_I,
                    weight_1=index_Q,
                    duration=integration_length,
                )
            )
            self._buses[element.bus].single_bin_counter += 1

    def _handle_conditional_trigger_prologue(self) -> None:
        """Push a qpysequence ``Conditional`` block for the bus validated by the Qblox pre-pass, ahead of this
        ``qp.if_trigger()`` block's children
        compiling. The ``Conditional`` itself unpacks into the ``set_cond``/``wait``/``latch_rst``
        sequence at qpysequence-compile time, self-timed so the "trigger missed" branch takes exactly
        as long as the "trigger received" branch -- see ``qpysequence.program.Conditional``.
        """
        # Only called for the qp.if_trigger() block, which the pre-pass found and validated
        conditional = cast("ConditionalTrigger", self._conditional)
        bus = conditional.bus
        trigger_network_wait = Wait(bus=bus, duration=conditional.trigger_padding_ns)
        self._handle_wait(trigger_network_wait)

        mask = _trigger_address_mask(QBLOXCONSTANTS.EXT_TRIGGER_ADDRESS)
        cond_block = QPyProgram.Conditional(QPyTriggerCondition.OR, mask)
        self._buses[bus].qpy_block_stack[-1].add(cond_block)
        self._buses[bus].qpy_block_stack.append(cond_block)

    def _handle_conditional_trigger_epilogue(self) -> None:
        """Pop the qpysequence ``Conditional`` block after a ``qp.if_trigger()`` block's children have
        compiled, then pad the bus back out to ``expected_trigger_wait_time`` (the QDAC's inter-trigger
        period) with a single plain, unconditional wait.

        The ``Conditional`` block already guarantees the "trigger missed" branch takes exactly as long
        as the "trigger received" branch, so both branches reach this point with the same elapsed time
        -- the padding below only needs to account for the (deterministic) total duration of the
        ``Conditional`` block itself, not for which branch actually ran.
        """
        conditional = cast("ConditionalTrigger", self._conditional)
        bus = conditional.bus
        # cond_block was already added to its parent in the prologue, while still empty, and has been
        # populated in place by reference during traversal since -- it must not be added again here.
        cond_block = self._buses[bus].qpy_block_stack.pop()

        expected_trigger_wait_time = conditional.expected_wait_time_ns
        trigger_padding_ns = conditional.trigger_padding_ns

        # cond_block.q1asm_duration is the block's guaranteed total real-time duration once lowered,
        # identical on both branches, straight from qpysequence (already correctly scaled for any
        # nested Average/ForLoop's iterations, and already accounting for the multi-instruction
        # expansion's own gated-padding and trailing latch_rst overhead).
        elapsed = trigger_padding_ns + cond_block.q1asm_duration
        padding = expected_trigger_wait_time - elapsed
        if padding < INST_MIN_WAIT:
            raise ValueError(
                f"The expected trigger wait time {expected_trigger_wait_time} must be at least {INST_MIN_WAIT} ns "
                f"greater than the elapsed duration {elapsed}, otherwise syncing cannot be maintained."
            )

        self._handle_wait(Wait(bus=bus, duration=padding))

        # The instructions qpysequence adds when lowering the Conditional (the skipped "not met" wait and the
        # trailing latch_rst) are never emitted by qililab, so their duration is counted here: the block's
        # lowered duration minus its body's.
        body_duration = sum(cast("int", component.q1asm_duration) for component in cond_block.components)
        overhead = cond_block.q1asm_duration - body_duration
        self._buses[bus].static_duration += overhead
        self._buses[bus].duration_since_sync += overhead

    def _handle_conditional(self, bus: str, enable: int, address: int, operator: int, else_duration: int) -> None:
        # The conditional does not add any static duration as it is assumed that the operations contained within are the same as the else_duration of the conditional

        mask = _trigger_address_mask(address)
        self._buses[bus].qpy_block_stack[-1].add(
            component=QPyInstructions.SetCond(enable, mask, operator, else_duration)
        )

        self._buses[bus].marked_for_sync = True

    def _handle_measure_reset(self, element: MeasureReset) -> None:
        """Executes a measurement followed by active reset in a single operation

        Args:
            element (MeasureReset): measure operation and perform active reset
        """

        time_of_flight = self._buses[element.bus].time_of_flight
        play = QbloxPlay(bus=element.bus, waveform=element.waveform, wait_time=time_of_flight)
        sync = Sync([element.bus, element.control_bus])
        wait = Wait(bus=element.control_bus, duration=WAIT_TRIGGER_NETWORK_INTERMODULES)
        play_reset_pulse = CorePlay(bus=element.control_bus, waveform=element.reset_pulse)

        self._handle_latch_rst(bus=element.control_bus, duration=INST_MIN_WAIT)
        self._handle_play(play)
        self._handle_acquire(element)
        self._handle_sync(sync)
        self._handle_wait(wait)
        self._handle_conditional(
            bus=element.control_bus,
            enable=ENABLE_CONDITIONAL,
            address=element.trigger_address,
            operator=QPyTriggerCondition.OR,
            else_duration=play_reset_pulse.waveform.get_duration(),  # type: ignore[union-attr]
        )
        self._handle_play(play_reset_pulse)
        self._handle_conditional(
            bus=element.control_bus, enable=DISABLE_CONDITIONAL, address=0, operator=0, else_duration=INST_MIN_WAIT
        )

    def _handle_play(self, element: "CorePlay | QbloxPlay") -> None:
        waveform_I, waveform_Q = _waveforms_of(element)
        if isinstance(element, QbloxPlay):
            # The qp.qblox.play() was used. Don't apply optimizations
            clamped = QbloxCompiler._clamp_duration(element.wait_time, label="play")
            duration = clamped
            index_I, index_Q, _ = self._append_to_waveforms_of_bus(
                bus=element.bus, waveform_I=waveform_I, waveform_Q=waveform_Q
            )
            self._buses[element.bus].qpy_block_stack[-1].add(
                component=QPyInstructions.Play(wave_0=index_I, wave_1=index_Q, duration=clamped)
            )
        elif (
            isinstance(waveform_I, Square)
            and (waveform_Q is None or isinstance(waveform_Q, Square))
            and (waveform_I.duration >= 100)
        ):
            copied_waveform_I: Square = deepcopy(waveform_I)
            copied_waveform_Q: Square | None = deepcopy(waveform_Q)
            duration = cast("int", copied_waveform_I.duration)
            chunk_duration, iterations, remainder = QbloxCompiler.calculate_square_waveform_optimization_values(
                duration
            )
            copied_waveform_I.duration = chunk_duration
            if isinstance(copied_waveform_Q, Square):
                copied_waveform_Q.duration = chunk_duration
            index_I, index_Q, _ = self._append_to_waveforms_of_bus(
                bus=element.bus, waveform_I=copied_waveform_I, waveform_Q=copied_waveform_Q
            )
            loop = QPyProgram.IterativeLoop(
                name=f"square_{self._buses[element.bus].waveform_optimization_counter}", iterations=iterations
            )
            loop.add(component=QPyInstructions.Play(wave_0=index_I, wave_1=index_Q, duration=chunk_duration))
            self._buses[element.bus].qpy_block_stack[-1].add(component=loop)
            if remainder != 0:
                copied_waveform_I.duration = remainder
                if isinstance(copied_waveform_Q, Square):
                    copied_waveform_Q.duration = remainder
                index_I, index_Q, _ = self._append_to_waveforms_of_bus(
                    bus=element.bus, waveform_I=copied_waveform_I, waveform_Q=copied_waveform_Q
                )
                self._buses[element.bus].qpy_block_stack[-1].add(
                    component=QPyInstructions.Play(wave_0=index_I, wave_1=index_Q, duration=remainder)
                )
            self._buses[element.bus].waveform_optimization_counter += 1
        elif (
            isinstance(waveform_I, FlatTop)
            and (waveform_Q is None or isinstance(waveform_Q, FlatTop))
            and ((waveform_I.duration - (waveform_I.smooth_duration + waveform_I.buffer) * 2) >= 100)
        ):
            smooth_waveform_I: FlatTop = deepcopy(waveform_I)
            smooth_waveform_Q: FlatTop | None = deepcopy(waveform_Q)
            duration = cast("int", smooth_waveform_I.duration)
            smooth_duration_I = (
                smooth_waveform_I.smooth_duration + smooth_waveform_I.buffer
                if smooth_waveform_I.smooth_duration + smooth_waveform_I.buffer > INST_MIN_WAIT
                else INST_MIN_WAIT
            )
            square_duration = cast("int", duration - smooth_duration_I * 2)

            inital_envelope_I = Arbitrary(samples=smooth_waveform_I.envelope()[:smooth_duration_I])
            end_envelope_I = Arbitrary(samples=smooth_waveform_I.envelope()[-smooth_duration_I:])
            inital_envelope_Q = None
            end_envelope_Q = None

            if isinstance(smooth_waveform_Q, FlatTop):
                if (
                    smooth_waveform_Q.smooth_duration + smooth_waveform_Q.buffer != smooth_duration_I
                    and smooth_duration_I != INST_MIN_WAIT
                ):
                    raise ValueError("smooth_duration + buffer of both I and Q must be the same.")
                inital_envelope_Q = Arbitrary(samples=smooth_waveform_Q.envelope()[:smooth_duration_I])
                end_envelope_Q = Arbitrary(samples=smooth_waveform_Q.envelope()[-smooth_duration_I:])

            index_I, index_Q, _ = self._append_to_waveforms_of_bus(
                bus=element.bus, waveform_I=inital_envelope_I, waveform_Q=inital_envelope_Q
            )
            self._buses[element.bus].qpy_block_stack[-1].add(
                component=QPyInstructions.Play(wave_0=index_I, wave_1=index_Q, duration=smooth_duration_I)
            )

            chunk_duration, iterations, remainder = QbloxCompiler.calculate_square_waveform_optimization_values(
                square_duration
            )
            square_waveform_I = Square(amplitude=smooth_waveform_I.amplitude, duration=chunk_duration)
            square_waveform_Q = None
            if isinstance(smooth_waveform_Q, FlatTop):
                square_waveform_Q = Square(amplitude=smooth_waveform_Q.amplitude, duration=chunk_duration)
            index_I, index_Q, _ = self._append_to_waveforms_of_bus(
                bus=element.bus, waveform_I=square_waveform_I, waveform_Q=square_waveform_Q
            )
            loop = QPyProgram.IterativeLoop(
                name=f"square_{self._buses[element.bus].waveform_optimization_counter}", iterations=iterations
            )
            loop.add(component=QPyInstructions.Play(wave_0=index_I, wave_1=index_Q, duration=chunk_duration))
            self._buses[element.bus].qpy_block_stack[-1].add(component=loop)
            if remainder != 0:
                square_waveform_I.duration = remainder
                if isinstance(smooth_waveform_Q, FlatTop):
                    square_waveform_Q.duration = remainder  # type: ignore [union-attr]
                index_I, index_Q, _ = self._append_to_waveforms_of_bus(
                    bus=element.bus, waveform_I=square_waveform_I, waveform_Q=square_waveform_Q
                )
                self._buses[element.bus].qpy_block_stack[-1].add(
                    component=QPyInstructions.Play(wave_0=index_I, wave_1=index_Q, duration=remainder)
                )

            index_I, index_Q, _ = self._append_to_waveforms_of_bus(
                bus=element.bus, waveform_I=end_envelope_I, waveform_Q=end_envelope_Q
            )
            self._buses[element.bus].qpy_block_stack[-1].add(
                component=QPyInstructions.Play(wave_0=index_I, wave_1=index_Q, duration=smooth_duration_I)
            )

            self._buses[element.bus].waveform_optimization_counter += 1
        else:
            index_I, index_Q, duration = self._append_to_waveforms_of_bus(
                bus=element.bus, waveform_I=waveform_I, waveform_Q=waveform_Q
            )
            self._buses[element.bus].qpy_block_stack[-1].add(
                component=QPyInstructions.Play(wave_0=index_I, wave_1=index_Q, duration=duration)
            )
        self._buses[element.bus].static_duration += duration
        self._buses[element.bus].duration_since_sync += duration
        self._buses[element.bus].marked_for_sync = True
        self._buses[element.bus].upd_param_instruction_pending = False

    def _get_or_create_weight_register(self, bus: str, weight_index: int, block_index: int) -> QPyProgram.Register:
        """Create or Retrieve a register for the weight index of the acquisition
            If it is the first weight index of this program with this value, then a new register is created and stored in the dictionary weight_index_to_register.
            If not, the register can be retrieved from the dictionary weight_index_to_register
        Args:
            bus (str): Name of the bus.
            weight_index (int): Weight index
            block_index (int): Position in qpy_block_stack to move the Register
        Returns:
            register (QPyProgram.Register): register to use to store the weight_index of the acquisition
        """
        if weight_index in self._buses[bus].weight_index_to_register:
            register = self._buses[bus].weight_index_to_register[weight_index]

        # no weight index with this value has been given before
        else:
            self._buses[bus].weight_index_to_register[weight_index] = QPyProgram.Register()
            register = self._buses[bus].weight_index_to_register[weight_index]
            self._buses[bus].qpy_block_stack[block_index]._add_structure(
                component=QPyInstructions.Move(source=weight_index, destination=register),
                insert_idx=0,
            )
        return register

    def _handle_block(self, element: Block) -> None:
        # No-op: registered only so the handler dispatch in traverse() doesn't raise;
        # traverse() recurses into Block children unconditionally right after calling this.
        pass

    @staticmethod
    def _get_reference_operation_of_loop(loop: Sweep, starting_block: Block | None = None) -> Operation | None:
        def collect_operations(block: Block):
            for element in block.elements:
                if isinstance(element, Block):
                    yield from collect_operations(element)
                elif loop.variable in element.variables():
                    yield element

        starting_block = starting_block or loop
        operations = list(collect_operations(starting_block))

        if not operations:
            return None
        return operations[0]

    @staticmethod
    def _get_qpysequence_conversion_instructions(
        operation: Operation | None,
    ) -> type[QPyInstructions.ConversionInstruction] | None:
        if operation is None:
            return None
        instruction_map: dict[type[Operation], type[QPyInstructions.ConversionInstruction] | None] = {
            SetFrequency: QPyInstructions.SetFrequencyHz,
            SetPhase: QPyInstructions.SetPhaseRad,
            SetGain: QPyInstructions.SetNormalisedGain,
            SetOffset: QPyInstructions.SetNormalisedOffs,
            Wait: None,
        }
        if type(operation) not in instruction_map:
            raise ValueError(f"{type(operation).__name__} does not support variable sweep in a loop.")
        return instruction_map[type(operation)]

    @staticmethod
    def _compute_loop_sweep(
        start: int | float, stop: int | float, step: int | float, scale_factor: float | int | None = None
    ) -> tuple[float, float, int]:
        iterations = for_loop_iterations(start, stop, step)
        if iterations == 1:
            # Single point: the formulas below divide by iterations - 1, which is 0. The loop runs once, so use a
            # step of 0: the register stays at start and no add/sub is written.
            return (start, 0, iterations)
        if scale_factor is None:
            qblox_step = (stop - start) / (iterations - 1)
            return (start, qblox_step, iterations)

        # Reproduce the pre-0.11 qpysequence rounding:
        start_int = int(start * scale_factor)
        stop_int = int(stop * scale_factor)
        step_int = (stop_int - start_int) // (iterations - 1)
        nudge = 0.5 if step_int >= 0 else -0.5
        qblox_step = (step_int + nudge) / scale_factor
        return (start, qblox_step, iterations)

    @staticmethod
    def _hash_waveform(waveform: Waveform) -> str:
        hashes = {
            key: (value.__dict__ if isinstance(value, Waveform) else value) for key, value in waveform.__dict__.items()
        }
        return f"{waveform.__class__.__name__} {hashes}"

    @staticmethod
    def calculate_square_waveform_optimization_values(duration: int) -> tuple[int, int, int]:
        def remainder_conditions(chunk_duration):
            remainder = duration % chunk_duration
            return remainder, (chunk_duration >= INST_MIN_WAIT and (remainder == 0 or remainder >= INST_MIN_WAIT))

        def find_chunk_duration(condition_func):
            for chunk_duration in range(100, 501):
                if chunk_duration <= duration:
                    remainder, valid = remainder_conditions(chunk_duration)
                    if valid and condition_func(remainder):
                        return chunk_duration
            return None

        # Make sure that duration ia an integer
        duration = int(duration)

        # First try for remainder == 0
        final_chunk_duration = find_chunk_duration(lambda rem: rem == 0)
        if final_chunk_duration is not None:
            return final_chunk_duration, duration // final_chunk_duration, duration % final_chunk_duration

        # If not found, try for remainder ≥ INST_MIN_WAIT
        final_chunk_duration = find_chunk_duration(lambda rem: rem >= INST_MIN_WAIT)
        if final_chunk_duration is not None:
            return final_chunk_duration, duration // final_chunk_duration, duration % final_chunk_duration

        # If no suitable piece_duration found, fallback to entire duration
        return duration, 1, 0
