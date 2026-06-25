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

"""Qblox compiler for the *new* ``qprogram`` AST.

New-AST counterpart of :mod:`qililab.qprogram.qblox_compiler`. It walks a
:class:`qprogram.qprogram.QProgram` and emits the same ``qpysequence`` artefacts the legacy compiler
produced, reusing the legacy :class:`~qililab.qprogram.qblox_compiler.QbloxCompilationOutput` /
:class:`~qililab.qprogram.qblox_compiler.AcquisitionData` containers so the existing upload / run /
acquire path consumes the output unchanged.

Ported features (parity with the legacy compiler):

* blocks ``Block`` / ``Average`` / ``ForLoop`` / ``Parallel`` and ops ``Play`` / ``Measure`` /
  qblox ``Acquire`` / ``Wait`` / ``Sync`` / ``SetFrequency`` / ``SetPhase`` / ``ResetPhase`` /
  ``SetGain`` / ``SetOffset``;
* Square / FlatTop **chunk optimisations** (long flats become a short played loop);
* **markers** (``SetMarkers`` + per-bus marker init from the ``markers`` argument);
* **trigger** (``SetTrigger`` + ``WaitTrigger``, gated by ``ext_trigger``);
* **active reset** (``ActiveReset`` → latch-reset / play / acquire / sync / conditional reset-pulse
  choreography; the readout bus is recorded in :attr:`QbloxCompilationOutput.trigger_network_required`
  so the platform can wire the trigger network);
* **dynamic (variable-duration) waits** and a dynamic-aware ``Sync`` for the common case
  (one dynamic loop variable shared across the synced buses).

Known boundaries (raise a clear ``NotImplementedError``, matching the legacy guards): two dynamic
waits without an intervening sync; expression-valued (``var ± const``) dynamic durations; more than
one *independent* dynamic bus in a single sync; the >32-acquisition exceeds-depth regime; crosstalk
pre-lowering. These are deliberately left to the legacy compiler / a future port.
"""

from __future__ import annotations

import math
from collections import deque
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Callable

import numpy as np
import qpysequence as QPy
import qpysequence.program as QPyProgram
import qpysequence.program.instructions as QPyInstructions
from qprogram.blocks import Average, Block, ForLoop, Loop, Parallel
from qprogram.operations import (
    Measure as CoreMeasure,
)
from qprogram.operations import (
    Play,
    ResetPhase,
    SetFrequency,
    SetGain,
    SetOffset,
    SetPhase,
    Sync,
    Wait,
)
from qprogram.variable import Expression, Variable
from qprogram.waveforms import Arbitrary, FlatTop, Square
from qprogram.waveforms.waveform import IQWaveform, Waveform
from qpysequence.constants import INST_MAX_WAIT, INST_MIN_WAIT

from qililab.config import logger
from qililab.qprogram.qblox_compiler import AcquisitionData, QbloxCompilationOutput

if TYPE_CHECKING:
    from qprogram.qprogram import QProgram

# Qblox vendor ops live in the vendor package; import lazily-safe (always present for qblox programs).
try:  # pragma: no cover - import guard
    from qprogram_qblox.operations import Acquire as QbloxAcquire
    from qprogram_qblox.operations import (
        ActiveReset,
        SetMarkers,
        SetTrigger,
        WaitTrigger,
    )
except ImportError:  # pragma: no cover
    QbloxAcquire = SetMarkers = SetTrigger = WaitTrigger = ActiveReset = None  # type: ignore[assignment, misc]

MAX_ACQUISITION_INDEX = 31  # 32 acquisition slots (0..31)
EXT_TRIGGER_ADDRESS = 15
ENABLE_CONDITIONAL = 1
DISABLE_CONDITIONAL = 0
AND_MASK_CONDITIONAL = 0


class _BusInfo:
    """Per-bus mutable compilation state (the new-AST ``BusCompilationInfo``)."""

    def __init__(self) -> None:
        self.qpy_sequence = QPy.Sequence(
            program=QPy.Program(), waveforms=QPy.Waveforms(), acquisitions=QPy.Acquisitions(), weights=QPy.Weights()
        )
        main_block = QPyProgram.Block(name="main")
        self.qpy_sequence._program.append_block(main_block)
        self.qpy_block_stack: deque[QPyProgram.Block] = deque([main_block])

        self.acquisitions: dict[str, AcquisitionData] = {}
        self.variable_to_register: dict[Variable, QPyProgram.Register] = {}
        self.waveform_to_index: dict[str, int] = {}
        self.weight_to_index: dict[str, int] = {}
        self.weight_index_to_register: dict[int, QPyProgram.Register] = {}

        self.loop_counter = 0
        self.average_counter = 0
        self.waveform_optimization_counter = 0
        self.acq_index_counter = 0

        self.static_duration = 0
        self.duration_since_sync = 0
        self.time_of_flight = QbloxCompilerV2.minimum_wait_duration

        # Real-time-parameter latching: an UpdParam must follow a Set* before a Wait.
        self.upd_param_instruction_pending = False
        # Sync bookkeeping.
        self.marked_for_sync = False
        self.marked_for_dynamic_sync = False
        self.dynamic_durations: list[Variable] = []
        self.dynamic_duration_register: QPyProgram.Register | None = None


class QbloxCompilerV2:
    """Compile a *new-AST* :class:`~qprogram.qprogram.QProgram` to ``qpysequence`` for Qblox."""

    minimum_wait_duration: int = 4

    def __init__(self) -> None:
        self._handlers: dict[type, Callable] = {
            Parallel: self._handle_parallel,
            Average: self._handle_average,
            ForLoop: self._handle_for_loop,
            Loop: self._handle_loop,
            SetFrequency: self._handle_set_frequency,
            SetPhase: self._handle_set_phase,
            ResetPhase: self._handle_reset_phase,
            SetGain: self._handle_set_gain,
            SetOffset: self._handle_set_offset,
            Wait: self._handle_wait,
            Sync: self._handle_sync,
            CoreMeasure: self._handle_measure,
            Play: self._handle_play,
            Block: self._handle_block,
        }
        if QbloxAcquire is not None:
            self._handlers[QbloxAcquire] = self._handle_acquire
            self._handlers[SetMarkers] = self._handle_set_markers
            self._handlers[SetTrigger] = self._handle_set_trigger
            self._handlers[WaitTrigger] = self._handle_wait_trigger
            self._handlers[ActiveReset] = self._handle_active_reset
        self._qprogram: QProgram
        self._buses: dict[str, _BusInfo] = {}
        self._qblox_buses: list[str] = []
        self._single_channel: list[str] = []
        self._markers: dict[str, str] | None = None
        self._ext_trigger: bool = False
        self._disable_autosync: bool = False
        self._latch_enabled: set[str] = set()
        self._trigger_network_required: dict[str, int] = {}
        self._active_reset_counter: int = 0

    # ------------------------------------------------------------------ entry point

    def compile(
        self,
        qprogram: QProgram,
        *,
        qblox_buses: list[str],
        single_channel: list[str] | None = None,
        times_of_flight: dict[str, int] | None = None,
        markers: dict[str, str] | None = None,
        ext_trigger: bool = False,
        disable_autosync: bool = False,
    ) -> QbloxCompilationOutput:
        """Compile ``qprogram`` to a :class:`~qililab.qprogram.qblox_compiler.QbloxCompilationOutput`.

        Args:
            qprogram: New-AST program (or HW sub-program). Buses must be Qblox aliases.
            qblox_buses: Bus aliases owned by Qblox modules; only these are compiled.
            single_channel: Bus aliases driven by a single-output sequencer (real, not IQ).
            times_of_flight: Per-bus time-of-flight in ns (used by ``measure``).
            markers: Per-bus initial marker mask (4-char binary string), computed by the platform from
                the module model / sequencer outputs. ``None`` → all markers off.
            ext_trigger: Whether the runcard enables an external trigger (gates ``wait_trigger``).
            disable_autosync: When ``True``, do not auto-insert a ``sync`` after each loop block.

        Returns:
            The compilation output. The extra attribute ``trigger_network_required`` (``dict`` mapping
            a readout bus alias → trigger address) tells the platform which buses need the Qblox
            trigger network set up before running (populated by ``active_reset``).
        """
        self._qprogram = qprogram
        self._qblox_buses = list(qblox_buses)
        self._single_channel = single_channel if single_channel is not None else []
        self._markers = markers
        self._ext_trigger = ext_trigger
        self._disable_autosync = disable_autosync
        self._latch_enabled = set()
        self._trigger_network_required = {}
        self._active_reset_counter = 0
        self._buses = {bus: _BusInfo() for bus in qprogram.buses if bus in self._qblox_buses}

        if times_of_flight is not None:
            for bus in self._buses.keys() & times_of_flight.keys():
                self._buses[bus].time_of_flight = times_of_flight[bus]

        # Buses that drive an active-reset conditional must enable latching at the very top.
        self._latch_enabled = self._collect_active_reset_control_buses(qprogram.body)

        # Per-bus initial markers + latch enable.
        for bus, info in self._buses.items():
            if bus in self._latch_enabled:
                info.qpy_block_stack[0].append_component(QPyInstructions.SetLatchEn(1, 4), 1)
            mask = self._markers[bus] if self._markers is not None and bus in self._markers else "0000"
            info.qpy_block_stack[0].append_component(component=QPyInstructions.SetMrk(int(mask, 2)))
            info.qpy_block_stack[0].append_component(component=QPyInstructions.UpdParam(4))
            info.static_duration += 4

        self._traverse(qprogram.body)

        sequences: dict[str, QPy.Sequence] = {}
        acquisitions: dict[str, dict[str, AcquisitionData]] = {}
        for bus, info in self._buses.items():
            info.qpy_block_stack[0].append_component(component=QPyInstructions.SetMrk(0))
            info.qpy_block_stack[0].append_component(component=QPyInstructions.UpdParam(4))
            info.qpy_block_stack[0].append_component(component=QPyInstructions.Stop())
            sequences[bus] = info.qpy_sequence
            acquisitions[bus] = info.acquisitions
        output = QbloxCompilationOutput(qprogram=qprogram, sequences=sequences, acquisitions=acquisitions)
        # Integration hook for the platform: which buses need the trigger network wired (active reset).
        output.trigger_network_required = dict(self._trigger_network_required)  # type: ignore[attr-defined]
        return output

    def _collect_active_reset_control_buses(self, block: Block) -> set[str]:
        """Pre-scan for ``ActiveReset`` ops; their control buses need latching enabled at the top."""
        control_buses: set[str] = set()
        if ActiveReset is None:
            return control_buses
        for element in block.walk():
            if isinstance(element, ActiveReset) and element.control_bus in self._buses:
                control_buses.add(element.control_bus)
        return control_buses

    # ------------------------------------------------------------------ traversal

    def _traverse(self, block: Block) -> None:
        for element in block.elements:
            handler = self._handlers.get(type(element))
            if handler is None:
                raise NotImplementedError(
                    f"{type(element).__name__} is not supported by the new-AST Qblox compiler (v2)."
                )
            appended = handler(element)
            if isinstance(element, Block):
                self._traverse(element)
                if not self._disable_autosync and isinstance(element, (ForLoop, Parallel, Average)):
                    self._handle_sync(Sync(targets=None), delay=True)
                if appended:
                    for info in self._buses.values():
                        info.qpy_block_stack.pop()

    # ------------------------------------------------------------------ blocks

    def _handle_block(self, _: Block) -> bool:
        return False

    def _handle_average(self, element: Average) -> bool:
        for info in self._buses.values():
            qpy_loop = QPyProgram.Loop(name=f"avg_{info.average_counter}", begin=element.shots)
            info.qpy_block_stack[-1].append_component(qpy_loop)
            info.qpy_block_stack.append(qpy_loop)
            info.average_counter += 1
        return True

    def _handle_for_loop(self, element: ForLoop) -> bool:
        reference = self._get_reference_operation_of_loop(element)
        start, step, iterations = self._convert_for_loop_values(element, reference)
        for info in self._buses.values():
            qpy_loop = QPyProgram.IterativeLoop(
                name=f"loop_{info.loop_counter}", iterations=iterations, loops=[(start, step)]
            )
            info.qpy_block_stack[-1].append_component(qpy_loop)
            info.qpy_block_stack.append(qpy_loop)
            info.variable_to_register[element.variable] = qpy_loop.loop_registers[0]
            info.loop_counter += 1
        return True

    def _handle_loop(self, _: Loop) -> bool:
        raise NotImplementedError("Loops over arbitrary numpy arrays are not supported for Qblox.")

    def _handle_parallel(self, element: Parallel) -> bool:
        if not element.loops:
            raise NotImplementedError("Parallel block should contain loops.")
        if any(isinstance(loop, Loop) for loop in element.loops):
            raise NotImplementedError("Loops over arbitrary numpy arrays are not supported for Qblox.")
        loops_params: list[tuple[int, int]] = []
        iterations_list: list[int] = []
        for loop in element.loops:
            reference = self._get_reference_operation_of_loop(loop, starting_block=element)
            start, step, iterations = self._convert_for_loop_values(loop, reference)
            loops_params.append((start, step))
            iterations_list.append(iterations)
        iterations = min(iterations_list)
        for info in self._buses.values():
            qpy_loop = QPyProgram.IterativeLoop(
                name=f"loop_{info.loop_counter}", iterations=iterations, loops=loops_params
            )
            for i, loop in enumerate(element.loops):
                info.variable_to_register[loop.variable] = qpy_loop.loop_registers[i]
            info.qpy_block_stack[-1].append_component(qpy_loop)
            info.qpy_block_stack.append(qpy_loop)
            info.loop_counter += 1
        return True

    # ------------------------------------------------------------------ real-time set-* ops

    def _handle_set_frequency(self, element: SetFrequency) -> None:
        if element.bus not in self._buses:
            return
        convert = self._convert_value(element)
        frequency = self._register_or_value(element.bus, element.frequency, convert)
        # Emitted twice to work around a Qblox bug where the first value inside a HW loop is wrong.
        self._append(element.bus, QPyInstructions.SetFreq(frequency=frequency))
        self._append(element.bus, QPyInstructions.SetFreq(frequency=frequency))
        self._buses[element.bus].upd_param_instruction_pending = True

    def _handle_set_phase(self, element: SetPhase) -> None:
        if element.bus not in self._buses:
            return
        convert = self._convert_value(element)
        phase = self._register_or_value(element.bus, element.phase, convert)
        self._append(element.bus, QPyInstructions.SetPh(phase=phase))
        self._buses[element.bus].upd_param_instruction_pending = True

    def _handle_reset_phase(self, element: ResetPhase) -> None:
        if element.bus not in self._buses:
            return
        self._append(element.bus, QPyInstructions.ResetPh())
        self._buses[element.bus].upd_param_instruction_pending = True

    def _handle_set_gain(self, element: SetGain) -> None:
        if element.bus not in self._buses:
            return
        convert = self._convert_value(element)
        gain = self._register_or_value(element.bus, element.gain, convert)
        self._append(element.bus, QPyInstructions.SetAwgGain(gain_0=gain, gain_1=gain))
        self._append(element.bus, QPyInstructions.SetAwgGain(gain_0=gain, gain_1=gain))
        self._buses[element.bus].upd_param_instruction_pending = True

    def _handle_set_offset(self, element: SetOffset) -> None:
        if element.bus not in self._buses:
            return
        convert = self._convert_value(element)
        offset_0 = self._register_or_value(element.bus, element.offset_path0, convert)
        offset_1 = (
            offset_0
            if element.offset_path1 is None
            else self._register_or_value(element.bus, element.offset_path1, convert)
        )
        self._append(element.bus, QPyInstructions.SetAwgOffs(offset_0=offset_0, offset_1=offset_1))
        self._buses[element.bus].upd_param_instruction_pending = True

    # ------------------------------------------------------------------ markers / triggers

    def _handle_set_markers(self, element: Any) -> None:
        if element.bus not in self._buses:
            return
        self._append(element.bus, QPyInstructions.SetMrk(marker_outputs=int(element.mask, 2)))
        self._buses[element.bus].upd_param_instruction_pending = True

    def _handle_set_trigger(self, element: Any) -> None:
        if element.bus not in self._buses:
            return
        mask = self._markers[element.bus] if self._markers is not None and element.bus in self._markers else "0000"
        if not element.outputs:
            raise ValueError("Missing qblox trigger outputs at set_trigger.")
        markers = list(mask)
        for output in element.outputs if isinstance(element.outputs, list) else [element.outputs]:
            if int(mask, 2) > 0:
                output_map = {1: 3, 2: 2}
                if output not in output_map:
                    raise ValueError("RF modules only have 2 trigger outputs, either 1 or 2")
            else:
                output_map = {1: 3, 2: 2, 3: 1, 4: 0}
                if output not in output_map:
                    raise ValueError("Low frequency modules only have 4 trigger outputs, out of range")
            markers[output_map[output]] = "1"
        self._append(element.bus, QPyInstructions.SetMrk(marker_outputs=int("".join(markers), 2)))
        self._buses[element.bus].upd_param_instruction_pending = True
        for bus in self._buses:
            self._handle_wait(Wait(bus=bus, duration=element.duration), delay=True)
        self._append(element.bus, QPyInstructions.SetMrk(marker_outputs=int(mask, 2)))
        self._buses[element.bus].upd_param_instruction_pending = True

    def _handle_wait_trigger(self, element: Any) -> None:
        if element.bus not in self._buses:
            return
        if isinstance(element.duration, (Variable, Expression)):
            raise ValueError("Wait trigger duration cannot be a Variable, it must be an int.")
        if not self._ext_trigger:
            raise AttributeError("External trigger has not been enabled in the runcard's instrument controllers.")
        port = element.port if element.port else EXT_TRIGGER_ADDRESS
        duration = int(max(element.duration, self.minimum_wait_duration))
        info = self._buses[element.bus]
        if info.upd_param_instruction_pending and self.minimum_wait_duration <= duration <= 8:
            self._append(element.bus, QPyInstructions.UpdParam(duration))
            self._append(element.bus, QPyInstructions.WaitTrigger(address=port, wait_time=self.minimum_wait_duration))
            info.upd_param_instruction_pending = False
        else:
            self._append(element.bus, QPyInstructions.WaitTrigger(address=port, wait_time=duration))
        info.static_duration += duration
        info.duration_since_sync += duration

    # ------------------------------------------------------------------ wait / sync

    def _handle_wait(self, element: Wait, *, delay: bool = False) -> None:
        if element.bus not in self._buses:
            return
        info = self._buses[element.bus]
        if isinstance(element.duration, Variable):
            if info.marked_for_dynamic_sync:
                raise NotImplementedError(
                    "Two dynamic (variable-duration) waits without a sync in between are not supported."
                )
            register = info.variable_to_register[element.duration]
            self._append(element.bus, QPyInstructions.Wait(register))
            if element.duration not in info.dynamic_durations:
                info.dynamic_durations.append(element.duration)
            info.dynamic_duration_register = register
            info.marked_for_dynamic_sync = True
        elif isinstance(element.duration, Expression):
            raise NotImplementedError(
                "Expression-valued (variable ± constant) wait durations are not yet ported to the v2 compiler."
            )
        else:
            convert = self._convert_value(element)
            duration = convert(element.duration)
            if not delay:
                info.duration_since_sync += duration
            self._add_wait(element.bus, duration)
        info.marked_for_sync = True

    def _handle_sync(self, element: Sync, *, delay: bool = False) -> None:
        """Align buses. Static padding for the common case; a basic dynamic-aware path when a single
        loop variable feeds the dynamic waits on every dynamic bus (each bus waits its own copy of the
        shared register). More complex static+dynamic mixing is delegated upstream (raises)."""
        targets = list(element.targets) if element.targets else list(self._buses.keys())
        targets = [bus for bus in targets if bus in self._buses]
        if len(targets) <= 1:
            for bus in targets:
                self._buses[bus].duration_since_sync = 0
                self._buses[bus].marked_for_sync = False
                self._buses[bus].marked_for_dynamic_sync = False
            return
        if not any(self._buses[bus].marked_for_sync or self._buses[bus].marked_for_dynamic_sync for bus in targets):
            return

        dynamic_buses = [bus for bus in targets if self._buses[bus].marked_for_dynamic_sync]
        if dynamic_buses:
            self._dynamic_sync(targets, dynamic_buses)
        else:
            self._static_sync(targets)

        for bus in targets:
            self._buses[bus].marked_for_sync = False
            self._buses[bus].marked_for_dynamic_sync = False
            self._buses[bus].duration_since_sync = 0

    def _static_sync(self, targets: list[str]) -> None:
        max_duration = max(self._buses[bus].duration_since_sync for bus in targets)
        for bus in targets:
            diff = max_duration - self._buses[bus].duration_since_sync
            if diff > 0:
                self._add_wait(bus, diff)

    def _dynamic_sync(self, targets: list[str], dynamic_buses: list[str]) -> None:
        """Basic dynamic sync: every dynamic bus must share the same single loop variable; each target
        replays that variable's per-bus register so all buses wait the same dynamic amount, then static
        differences are padded. Anything more intricate is out of scope for the v2 compiler."""
        dynamic_vars = {var for bus in dynamic_buses for var in self._buses[bus].dynamic_durations}
        if len(dynamic_vars) != 1:
            raise NotImplementedError(
                "Dynamic sync across buses with different/multiple dynamic-duration variables is not supported."
            )
        shared_var = next(iter(dynamic_vars))
        # First equalise the static parts.
        self._static_sync(targets)
        # Then every non-dynamic target waits the same dynamic amount via its own register copy.
        for bus in targets:
            if bus in dynamic_buses:
                continue
            register = self._buses[bus].variable_to_register.get(shared_var)
            if register is None:
                raise NotImplementedError(
                    "Dynamic sync requires the dynamic-duration variable to be in scope on every synced bus."
                )
            self._append(bus, QPyInstructions.Wait(register))

    # ------------------------------------------------------------------ play / measure / acquire

    def _handle_play(self, element: Play, wait_time: int | None = None) -> None:
        if element.bus not in self._buses:
            return
        if self._waveform_has_variable(element.waveform):
            logger.error("Variables in waveforms are not supported in Qblox.")
            return
        waveform_i, waveform_q = self._split_waveform(element.waveform)
        info = self._buses[element.bus]

        # Square / FlatTop chunk optimisation (only for a plain play, not a fixed-duration readout play).
        if wait_time is None and self._try_play_optimized(element.bus, waveform_i, waveform_q):
            info.upd_param_instruction_pending = False
            return

        index_i, index_q, length = self._append_to_waveforms_of_bus(element.bus, waveform_i, waveform_q)
        duration = length if wait_time is None else wait_time
        duration = int(max(duration, self.minimum_wait_duration))
        self._append(element.bus, QPyInstructions.Play(index_i, index_q, wait_time=duration))
        info.static_duration += duration
        info.duration_since_sync += duration
        info.upd_param_instruction_pending = False

    def _try_play_optimized(self, bus: str, waveform_i: Waveform, waveform_q: Waveform | None) -> bool:
        """Emit a chunked play loop for long Square / FlatTop waveforms. Returns True when handled."""
        info = self._buses[bus]
        if (
            isinstance(waveform_i, Square)
            and (waveform_q is None or isinstance(waveform_q, Square))
            and (waveform_i.duration >= 100)
        ):
            wf_i = deepcopy(waveform_i)
            wf_q = deepcopy(waveform_q)
            total = int(wf_i.duration)
            chunk, iterations, remainder = self.calculate_square_waveform_optimization_values(total)
            wf_i.duration = chunk
            if isinstance(wf_q, Square):
                wf_q.duration = chunk
            index_i, index_q, _ = self._append_to_waveforms_of_bus(bus, wf_i, wf_q)
            loop = QPyProgram.IterativeLoop(name=f"square_{info.waveform_optimization_counter}", iterations=iterations)
            loop.append_component(component=QPyInstructions.Play(index_i, index_q, wait_time=chunk))
            info.qpy_block_stack[-1].append_component(component=loop)
            if remainder != 0:
                wf_i.duration = remainder
                if isinstance(wf_q, Square):
                    wf_q.duration = remainder
                index_i, index_q, _ = self._append_to_waveforms_of_bus(bus, wf_i, wf_q)
                self._append(bus, QPyInstructions.Play(index_i, index_q, wait_time=remainder))
            info.waveform_optimization_counter += 1
            info.static_duration += total
            info.duration_since_sync += total
            return True
        if (
            isinstance(waveform_i, FlatTop)
            and (waveform_q is None or isinstance(waveform_q, FlatTop))
            and ((waveform_i.duration - (waveform_i.smooth_duration + waveform_i.buffer) * 2) >= 100)
        ):
            self._play_flat_top(bus, waveform_i, waveform_q)
            return True
        return False

    def _play_flat_top(self, bus: str, waveform_i: FlatTop, waveform_q: FlatTop | None) -> None:
        info = self._buses[bus]
        total = int(waveform_i.duration)
        edge = waveform_i.smooth_duration + waveform_i.buffer
        edge = edge if edge > INST_MIN_WAIT else INST_MIN_WAIT
        square_duration = total - edge * 2

        init_i = Arbitrary(samples=waveform_i.envelope()[:edge])
        end_i = Arbitrary(samples=waveform_i.envelope()[-edge:])
        init_q = end_q = None
        if isinstance(waveform_q, FlatTop):
            if waveform_q.smooth_duration + waveform_q.buffer != edge and edge != INST_MIN_WAIT:
                raise ValueError("smooth_duration + buffer of both I and Q must be the same.")
            init_q = Arbitrary(samples=waveform_q.envelope()[:edge])
            end_q = Arbitrary(samples=waveform_q.envelope()[-edge:])

        index_i, index_q, _ = self._append_to_waveforms_of_bus(bus, init_i, init_q)
        self._append(bus, QPyInstructions.Play(index_i, index_q, wait_time=edge))

        chunk, iterations, remainder = self.calculate_square_waveform_optimization_values(square_duration)
        sq_i: Waveform = Square(amplitude=waveform_i.amplitude, duration=chunk)
        sq_q: Waveform | None = (
            Square(amplitude=waveform_q.amplitude, duration=chunk) if isinstance(waveform_q, FlatTop) else None
        )
        index_i, index_q, _ = self._append_to_waveforms_of_bus(bus, sq_i, sq_q)
        loop = QPyProgram.IterativeLoop(name=f"square_{info.waveform_optimization_counter}", iterations=iterations)
        loop.append_component(component=QPyInstructions.Play(index_i, index_q, wait_time=chunk))
        info.qpy_block_stack[-1].append_component(component=loop)
        if remainder != 0:
            sq_i = Square(amplitude=waveform_i.amplitude, duration=remainder)
            sq_q = (
                Square(amplitude=waveform_q.amplitude, duration=remainder) if isinstance(waveform_q, FlatTop) else None
            )
            index_i, index_q, _ = self._append_to_waveforms_of_bus(bus, sq_i, sq_q)
            self._append(bus, QPyInstructions.Play(index_i, index_q, wait_time=remainder))

        index_i, index_q, _ = self._append_to_waveforms_of_bus(bus, end_i, end_q)
        self._append(bus, QPyInstructions.Play(index_i, index_q, wait_time=edge))
        info.waveform_optimization_counter += 1
        info.static_duration += total
        info.duration_since_sync += total

    def _handle_measure(self, element: CoreMeasure) -> None:
        if element.bus not in self._buses:
            return
        time_of_flight = self._buses[element.bus].time_of_flight
        self._handle_play(Play(bus=element.bus, waveform=element.waveform), wait_time=time_of_flight)
        self._emit_acquire(element.bus, element.weights, element.handle.name, save_adc="raw" in element.returns)

    def _handle_acquire(self, element: Any) -> None:
        if element.bus not in self._buses:
            return
        self._emit_acquire(element.bus, element.weights, element.handle.name, save_adc="raw" in element.returns)

    def _emit_acquire(self, bus: str, weights: IQWaveform, name: str, save_adc: bool) -> None:
        info = self._buses[bus]
        index_i, index_q, integration_length = self._append_to_weights_of_bus(bus, weights)
        loops = [(i, lp) for i, lp in enumerate(info.qpy_block_stack) if isinstance(lp, QPyProgram.IterativeLoop)]
        shape = tuple(lp.iterations for _, lp in loops)
        num_bins = int(math.prod(lp.iterations for _, lp in loops)) if loops else 1

        acq_index = info.acq_index_counter
        info.acq_index_counter += 1
        if acq_index > MAX_ACQUISITION_INDEX:
            raise NotImplementedError(
                f"Bus '{bus}' uses more than {MAX_ACQUISITION_INDEX + 1} acquisition indices; the >32-acquisition "
                "exceeds-depth regime is not ported to the v2 compiler."
            )
        info.acquisitions[name] = AcquisitionData(bus=bus, save_adc=save_adc, shape=shape, intertwined=1)
        info.qpy_sequence._acquisitions.add(name=name, num_bins=num_bins, index=acq_index)

        if num_bins > 1:
            move_block_index = loops[0][0] - 1
            add_block_index = loops[-1][0]
            bin_register = QPyProgram.Register()
            info.qpy_block_stack[move_block_index].append_component(
                component=QPyInstructions.Move(var=0, register=bin_register),
                bot_position=len(info.qpy_block_stack[move_block_index].components),
            )
            register_i = self._get_or_create_weight_register(bus, index_i, move_block_index)
            register_q = self._get_or_create_weight_register(bus, index_q, move_block_index)
            info.qpy_block_stack[-1].append_component(
                component=QPyInstructions.AcquireWeighed(
                    acq_index=acq_index,
                    bin_index=bin_register,
                    weight_index_0=register_i,
                    weight_index_1=register_q,
                    wait_time=integration_length,
                )
            )
            info.qpy_block_stack[add_block_index].append_component(
                component=QPyInstructions.Add(origin=bin_register, var=1, destination=bin_register)
            )
        else:
            info.qpy_block_stack[-1].append_component(
                component=QPyInstructions.AcquireWeighed(
                    acq_index=acq_index,
                    bin_index=0,
                    weight_index_0=index_i,
                    weight_index_1=index_q,
                    wait_time=integration_length,
                )
            )
        info.static_duration += integration_length
        info.duration_since_sync += integration_length
        info.marked_for_sync = True
        info.upd_param_instruction_pending = False

    # ------------------------------------------------------------------ active reset (feedback)

    def _handle_conditional(self, bus: str, enable: int, mask: int, operator: int, else_duration: int) -> None:
        self._append(bus, QPyInstructions.SetCond(enable, mask, operator, else_duration))
        self._buses[bus].marked_for_sync = True

    def _handle_latch_rst(self, bus: str, duration: int) -> None:
        self._append(bus, QPyInstructions.LatchRst(wait_time=duration))
        self._buses[bus].marked_for_sync = True
        self._buses[bus].duration_since_sync += duration
        self._buses[bus].static_duration += duration

    def _handle_active_reset(self, element: Any) -> None:
        """Port of the legacy ``measure_reset`` choreography: latch-reset, play+acquire the readout,
        sync with the control bus, wait for the trigger network, then conditionally play the reset pulse."""
        if element.bus not in self._buses or element.control_bus not in self._buses:
            return
        wait_trigger_network = 400  # conservative ns for the qblox trigger network (guideline ~388 ns)
        mask = 2 ** (element.trigger_address - 1)
        self._trigger_network_required[element.bus] = element.trigger_address

        reset_duration = self._waveform_duration(element.reset_pulse)
        name = f"{element.bus}/_active_reset_{self._active_reset_counter}"
        self._active_reset_counter += 1

        self._handle_latch_rst(bus=element.control_bus, duration=self.minimum_wait_duration)
        time_of_flight = self._buses[element.bus].time_of_flight
        self._handle_play(Play(bus=element.bus, waveform=element.waveform), wait_time=time_of_flight)
        self._emit_acquire(element.bus, element.weights, name, save_adc=False)
        self._handle_sync(Sync(targets=[element.bus, element.control_bus]))
        self._handle_wait(Wait(bus=element.control_bus, duration=wait_trigger_network))
        self._handle_conditional(
            bus=element.control_bus,
            enable=ENABLE_CONDITIONAL,
            mask=mask,
            operator=AND_MASK_CONDITIONAL,
            else_duration=reset_duration,
        )
        self._handle_play(Play(bus=element.control_bus, waveform=element.reset_pulse))
        self._handle_conditional(
            bus=element.control_bus, enable=DISABLE_CONDITIONAL, mask=0, operator=0, else_duration=4
        )

    # ------------------------------------------------------------------ waveforms / weights

    def _append_to_waveforms_of_bus(
        self, bus: str, waveform_i: Waveform, waveform_q: Waveform | None
    ) -> tuple[int, int, int]:
        def handle_waveform(waveform: Waveform | None, default_length: int = 0) -> tuple[int, int]:
            _hash = self._hash_waveform(waveform) if waveform is not None else f"zeros {default_length}"
            if _hash in self._buses[bus].waveform_to_index:
                index = self._buses[bus].waveform_to_index[_hash]
                length = next(
                    len(wf.data) for wf in self._buses[bus].qpy_sequence._waveforms._waveforms if wf.index == index
                )
                return index, length
            envelope = waveform.envelope() if waveform is not None else np.zeros(default_length)
            index = self._buses[bus].qpy_sequence._waveforms.add(envelope)
            self._buses[bus].waveform_to_index[_hash] = index
            return index, len(envelope)

        index_i, length_i = handle_waveform(waveform_i, 0)
        if waveform_q is None and bus in self._single_channel:
            index_q, _ = handle_waveform(waveform_i, 0)
        else:
            index_q, _ = handle_waveform(waveform_q, len(waveform_i.envelope()))
        return index_i, index_q, length_i

    def _append_to_weights_of_bus(self, bus: str, weights: IQWaveform) -> tuple[int, int, int]:
        def handle_weight(waveform: Waveform) -> tuple[int, int]:
            _hash = self._hash_waveform(waveform)
            if _hash in self._buses[bus].weight_to_index:
                index = self._buses[bus].weight_to_index[_hash]
                length = next(
                    len(weight.data)
                    for weight in self._buses[bus].qpy_sequence._weights._weights
                    if weight.index == index
                )
                return index, length
            envelope = waveform.envelope()
            index = self._buses[bus].qpy_sequence._weights.add(envelope)
            self._buses[bus].weight_to_index[_hash] = index
            return index, len(envelope)

        index_i, length_i = handle_weight(weights.get_I())
        index_q, _ = handle_weight(weights.get_Q())
        return index_i, index_q, length_i

    def _get_or_create_weight_register(self, bus: str, weight_index: int, block_index: int) -> QPyProgram.Register:
        info = self._buses[bus]
        if weight_index in info.weight_index_to_register:
            return info.weight_index_to_register[weight_index]
        register = QPyProgram.Register()
        info.weight_index_to_register[weight_index] = register
        info.qpy_block_stack[block_index].append_component(
            component=QPyInstructions.Move(var=weight_index, register=register),
            bot_position=len(info.qpy_block_stack[block_index].components),
        )
        return register

    # ------------------------------------------------------------------ helpers

    def _append(self, bus: str, component: Any) -> None:
        self._buses[bus].qpy_block_stack[-1].append_component(component=component)

    def _add_wait(self, bus: str, duration: int) -> None:
        duration = int(duration)
        while duration > INST_MAX_WAIT:
            self._append(bus, QPyInstructions.Wait(INST_MAX_WAIT))
            duration -= INST_MAX_WAIT
        if duration >= self.minimum_wait_duration:
            self._append(bus, QPyInstructions.Wait(duration))
        self._buses[bus].static_duration += int(duration)

    def _register_or_value(self, bus: str, value: Any, convert: Callable[[Any], int]) -> Any:
        if isinstance(value, Variable):
            return self._buses[bus].variable_to_register[value]
        if isinstance(value, Expression):
            raise NotImplementedError(
                "Expression-valued real-time parameters are not yet supported by the v2 compiler "
                "(use a plain loop Variable or a constant)."
            )
        return convert(value)

    @staticmethod
    def _split_waveform(waveform: Waveform | IQWaveform | str) -> tuple[Waveform, Waveform | None]:
        if isinstance(waveform, str):
            raise NotImplementedError("String waveform aliases must be resolved before compilation.")
        if isinstance(waveform, IQWaveform):
            return waveform.get_I(), waveform.get_Q()
        return waveform, None

    @staticmethod
    def _waveform_duration(waveform: Waveform | IQWaveform | str) -> int:
        if isinstance(waveform, str):
            raise NotImplementedError("String waveform aliases must be resolved before compilation.")
        return int(waveform.get_duration())

    @staticmethod
    def _waveform_has_variable(waveform: Waveform | IQWaveform | str) -> bool:
        if isinstance(waveform, str):
            return False

        def has_var(value: Any) -> bool:
            if isinstance(value, (Variable, Expression)):
                return True
            if isinstance(value, (Waveform, IQWaveform)):
                return any(has_var(v) for k, v in vars(value).items() if not k.startswith("_"))
            return False

        return has_var(waveform)

    def _get_reference_operation_of_loop(self, loop: ForLoop | Loop, starting_block: Block | None = None) -> Any:
        def collect(block: Block) -> Any:
            for element in block.elements:
                if isinstance(element, Block):
                    yield from collect(element)
                elif loop.variable in element.variables():
                    yield element

        operations = list(collect(starting_block if starting_block is not None else loop))
        return operations[0] if operations else None

    def _convert_for_loop_values(self, for_loop: ForLoop, operation: Any) -> tuple[int, int, int]:
        convert = self._convert_value(operation)
        iterations = for_loop.num_iterations()
        qblox_start = convert(for_loop.start)
        qblox_stop = convert(for_loop.stop)
        qblox_step = (qblox_stop - qblox_start) // (iterations - 1) if iterations > 1 else 0
        return (qblox_start, qblox_step, iterations)

    @staticmethod
    def _convert_value(operation: Any) -> Callable[[Any], int]:
        conversion_map: dict[type, Callable[[Any], int]] = {
            SetFrequency: lambda x: int(x * 4),
            SetPhase: lambda x: int(x * 1e9 / (2 * np.pi)),
            SetGain: lambda x: int(x * 32_767),
            SetOffset: lambda x: int(x * 32_767),
            Wait: lambda x: int(max(x, QbloxCompilerV2.minimum_wait_duration)),
            Play: lambda x: int(max(x, QbloxCompilerV2.minimum_wait_duration)),
        }
        return conversion_map.get(type(operation), lambda x: int(x))

    @staticmethod
    def _hash_waveform(waveform: Waveform) -> str:
        hashes = {
            key: (value.__dict__ if isinstance(value, Waveform) else value) for key, value in waveform.__dict__.items()
        }
        return f"{waveform.__class__.__name__} {hashes}"

    @staticmethod
    def calculate_square_waveform_optimization_values(duration: int) -> tuple[int, int, int]:
        duration = int(duration)

        def remainder_ok(chunk: int) -> tuple[int, bool]:
            remainder = duration % chunk
            return remainder, (chunk >= 4 and (remainder == 0 or remainder >= 4))

        def find_chunk(condition: Callable[[int], bool]) -> int | None:
            for chunk in range(100, 501):
                if chunk <= duration:
                    remainder, valid = remainder_ok(chunk)
                    if valid and condition(remainder):
                        return chunk
            return None

        chunk = find_chunk(lambda rem: rem == 0)
        if chunk is not None:
            return chunk, duration // chunk, duration % chunk
        chunk = find_chunk(lambda rem: rem >= 4)
        if chunk is not None:
            return chunk, duration // chunk, duration % chunk
        return duration, 1, 0
