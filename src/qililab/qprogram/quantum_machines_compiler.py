import hashlib
import math
from collections import deque
from typing import Any, Callable

import numpy as np
import qm.qua as qua

from qililab.qprogram.blocks import Average, Block, ForLoop, Loop, Parallel
from qililab.qprogram.operations import (
    Acquire,
    Operation,
    Play,
    ResetPhase,
    SetFrequency,
    SetGain,
    SetOffset,
    SetPhase,
    Sync,
    Wait,
)
from qililab.qprogram.qprogram import QProgram
from qililab.qprogram.variable import Domain, Variable
from qililab.waveforms import IQPair, Square, Waveform


# pylint: disable=protected-access
class CompilationInfo:  # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """Class representing the information stored by QBloxCompiler for a bus."""

    def __init__(self):
        # The generated Sequence
        self.qua_program = qua.program()


class BusCompilationInfo:
    def __init__(self):
        self.current_gain: float | qua.QuaVariableType | None = None
        self.current_frequency: float | None = None


class QuantumMachinesCompiler:
    """_summary_"""

    def __init__(self):
        # Handlers to map each operation to a corresponding handler function
        self._handlers: dict[type, Callable] = {
            ForLoop: self._handle_for_loop,
            Loop: self._handle_loop,
            Play: self._handle_play,
            SetFrequency: self._handle_set_frequency,
            SetGain: self._handle_set_gain,
            Wait: self._handle_wait,
        }

        self._buses: dict[str, BusCompilationInfo]

        self._qprogram: QProgram
        self._qprogram_block_stack: deque[Block] = deque()
        self._qprogram_to_qua_variables: dict[Variable, qua.QuaVariableType] = {}

        self._configuration: dict = {
            "waveforms": {},
            "pulses": {},
            "integration_weights": {},
            "digital_waveforms": {"ON": {"samples": [(1, 0)]}},
            "operations": {},
        }

    def compile(self, qprogram: QProgram) -> tuple[qua.Program, dict]:
        """Compile QProgram to QUA's Program.

        Args:
            qprogram (QProgram): The QProgram to be compiled

        Returns:
            qua.Program: The compiled program.
        """

        def traverse(block: Block):
            self._qprogram_block_stack.append(block)
            for element in block.elements:
                handler = self._handlers.get(type(element))
                if not handler:
                    raise NotImplementedError(f"{element.__class__} is currently not supported in Quantum Machines.")
                if isinstance(element, (ForLoop, Loop, Average, Parallel)):
                    with handler(element):
                        traverse(element)
                elif isinstance(element, Block):
                    traverse(element)
                else:
                    handler(element)
            self._qprogram_block_stack.pop()

        self._qprogram = qprogram
        self._buses = self._populate_buses()

        with qua.program() as qua_program:
            # Declare variables
            self._declare_variables()
            # Recursive traversal to convert QProgram blocks to Sequence
            traverse(self._qprogram._program)

        # Return a dictionary with bus names as keys and the compiled Sequence as values.
        return qua_program, self._configuration

    def _declare_variables(self):
        for variable in self._qprogram._variables:
            if variable.domain in [Domain.Time, Domain.Frequency]:
                qua_variable = qua.declare(int)
            else:
                qua_variable = qua.declare(qua.fixed)
            self._qprogram_to_qua_variables[variable] = qua_variable

    def _populate_buses(self):
        """Map each bus in the QProgram to a BusCompilationInfo instance.

        Returns:
            A dictionary where the keys are bus names and the values are BusCompilationInfo objects.
        """

        def collect_buses(block: Block):
            for element in block.elements:
                if isinstance(element, Block):
                    yield from collect_buses(element)
                if isinstance(element, Operation):
                    bus = getattr(element, "bus", None)
                    if bus:
                        yield bus

        buses = set(collect_buses(self._qprogram._program))
        return {bus: BusCompilationInfo() for bus in buses}

    def _handle_for_loop(self, element: ForLoop):
        qua_variable = self._qprogram_to_qua_variables[element.variable]
        return qua.for_(qua_variable, element.start, qua_variable <= element.stop, qua_variable + element.step)

    def _handle_loop(self, element: Loop):
        qua_variable = self._qprogram_to_qua_variables[element.variable]
        return qua.for_each_(qua_variable, element.values)

    def _handle_set_frequency(self, element: SetFrequency):
        frequency = (
            self._qprogram_to_qua_variables[element.frequency]
            if isinstance(element.frequency, Variable)
            else element.frequency
        )
        qua.update_frequency(element=element.bus, new_frequency=frequency * 1e3, units="mHz")

    def _handle_set_gain(self, element: SetGain):
        gain = self._qprogram_to_qua_variables[element.gain] if isinstance(element.gain, Variable) else element.gain
        # QUA doesn't have a method for setting the gain directly.
        # Instead, it uses an amplitude multiplication with `amp()`.
        # Thus, we store the current gain to multiply with in the next play instructions.
        self._buses[element.bus].current_gain = gain

    def _handle_play(self, element: Play):
        waveform_I, waveform_Q = element.get_waveforms()
        waveform_variables = element.get_waveform_variables()
        if not waveform_variables:
            hash_I = QuantumMachinesCompiler._hash_waveform(waveform=waveform_I)
            if hash_I not in self._configuration["waveforms"]:
                self._configuration["waveforms"][hash_I] = QuantumMachinesCompiler._to_config(waveform=waveform_I)
            if waveform_Q:
                hash_Q = QuantumMachinesCompiler._hash_waveform(waveform=waveform_Q)
                if hash_Q not in self._configuration["waveforms"]:
                    self._configuration["waveforms"][hash_Q] = QuantumMachinesCompiler._to_config(waveform=waveform_Q)
                pulse_hash = f"control_{hash_I}_{hash_Q}_{waveform_I.get_duration()}"
                if pulse_hash not in self._configuration["pulses"]:
                    self._configuration["pulses"][pulse_hash] = {
                        "operation": "control",
                        "length": waveform_I.get_duration(),
                        "waveforms": {
                            "I": hash_I,
                            "Q": hash_Q,
                        },
                    }
            else:
                pulse_hash = f"control_{hash_I}_{waveform_I.get_duration()}"
                if pulse_hash not in self._configuration["pulses"]:
                    self._configuration["pulses"][pulse_hash] = {
                        "operation": "control",
                        "length": waveform_I.get_duration(),
                        "waveforms": {
                            "single": hash_I,
                        },
                    }

            if element.bus not in self._configuration["operations"]:
                self._configuration["operations"][element.bus] = {}
            if pulse_hash not in self._configuration["operations"][element.bus]:
                self._configuration["operations"][element.bus][pulse_hash] = pulse_hash

            if self._buses[element.bus].current_gain is not None:
                qua.play(pulse=pulse_hash * qua.amp(self._buses[element.bus].current_gain), element=element.bus)
            else:
                qua.play(pulse=pulse_hash, element=element.bus)

    def _handle_wait(self, element: Wait):
        duration = (
            self._qprogram_to_qua_variables[element.duration]
            if isinstance(element.duration, Variable)
            else element.duration
        )
        qua.wait(duration, element.bus)

    @staticmethod
    def _hash_waveform(waveform: Waveform):
        attributes = [
            f"{key}: {(QuantumMachinesCompiler._hash_waveform(value) if isinstance(value, Waveform) else str(value))}"
            for key, value in waveform.__dict__.items()
            if key != "duration"
        ]
        string_to_hash = f"{waveform.__class__.__name__}({','.join(attributes)})"
        hash_result = hashlib.md5(string_to_hash.encode("utf-8"), usedforsecurity=False)
        return hash_result.hexdigest()[:10]

    @staticmethod
    def _to_config(waveform: Waveform):
        if isinstance(waveform, Square):
            return {"type": "constant", "sample": waveform.amplitude}
        else:
            return {"type": "arbitrary", "samples": waveform.envelope().tolist()}
