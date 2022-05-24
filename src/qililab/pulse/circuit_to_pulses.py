"""Class that translates a Qibo Circuit into a PulseSequence"""
from dataclasses import dataclass

import numpy as np
from qibo.abstractions.gates import Gate
from qibo.core.circuit import Circuit
from qibo.gates import RX, RY, RZ, I, M, X, Y, Z

from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_sequences import PulseSequences
from qililab.pulse.pulse_shape import Drag
from qililab.pulse.readout_pulse import ReadoutPulse
from qililab.utils import nested_dataclass


@dataclass
class CircuitToPulses:
    """Class that translates a Qibo Circuit into a PulseSequence"""

    @nested_dataclass
    class CircuitToPulsesSettings:
        """Settings of the CircuitToPulses class."""

        @dataclass
        class ReadoutPulseSettings:
            """ReadoutPulseSettings class."""

            amplitude: float = 0.4
            duration: int = 2000
            phase: float = 0

        readout_pulse = ReadoutPulseSettings()
        delay_between_pulses: int = 0
        delay_before_readout: int = 50
        gate_duration: int = 100
        num_sigmas: float = 4
        drag_coefficient: float = 0

    settings: CircuitToPulsesSettings

    def translate(self, circuit: Circuit) -> PulseSequences:
        """Translate a circuit into a pulse sequence.

        Args:
            circuit (Circuit): Qibo Circuit class.

        Returns:
            PulseSequences: Object containing the translated pulses.
        """
        sequence = PulseSequences(
            delay_between_pulses=self.delay_between_pulses, delay_before_readout=self.delay_before_readout
        )
        gates = list(circuit.queue)
        if circuit.measurement_gate is not None:
            gates.append(circuit.measurement_gate)
        for gate in gates:
            if isinstance(gate, M):
                for qubit_id in gate.target_qubits:
                    sequence.add(
                        ReadoutPulse(
                            amplitude=self.readout_pulse.amplitude,
                            phase=self.readout_pulse.phase,
                            duration=self.readout_pulse.duration,
                            qubit_ids=[qubit_id],
                        )
                    )
            else:
                sequence.add(self._gate_to_pulse(gate=gate))
        return sequence

    def _gate_to_pulse(self, gate: Gate):
        """Translate a gate into a pulse.

        Args:
            gate (Gate): Qibo Gate.

        Returns:
            Pulse: Pulse object.
        """
        if isinstance(gate, I):
            amplitude = 0.0
            phase = 0.0
        elif isinstance(gate, X):
            amplitude = 1
            phase = 0.0
        elif isinstance(gate, Y):
            amplitude = 1
            phase = np.pi / 2
        elif isinstance(gate, RX):
            theta = gate.parameters
            theta = (theta) % (2 * np.pi)
            if theta > np.pi:
                theta -= 2 * np.pi
            amplitude = np.abs(theta) / np.pi
            phase = 0 if theta >= 0 else np.pi
        elif isinstance(gate, RY):
            theta = gate.parameters
            theta = (theta) % (2 * np.pi)
            if theta > np.pi:
                theta -= 2 * np.pi
            amplitude = np.abs(theta) / np.pi
            phase = np.pi / 2 if theta >= 0 else 3 * np.pi / 4
        else:
            raise ValueError(f"Qililab has not defined a gate {gate.__class__.__name__}")
        return Pulse(
            amplitude=amplitude,
            phase=phase,
            duration=self.gate_duration,
            qubit_ids=list(gate.target_qubits),
            pulse_shape=Drag(num_sigmas=self.num_sigmas, beta=self.drag_coefficient),
        )

    @property
    def delay_between_pulses(self):
        """CircuitToPulse 'delay_between_pulses' property.

        Returns:
            int: settings.delay_between_pulses.
        """
        return self.settings.delay_between_pulses

    @property
    def delay_before_readout(self):
        """CircuitToPulse 'delay_before_readout' property.

        Returns:
            int: settings.delay_before_readout.
        """
        return self.settings.delay_before_readout

    @property
    def num_sigmas(self):
        """CircuitToPulse 'num_sigmas' property.

        Returns:
            float: settings.num_sigmas.
        """
        return self.settings.num_sigmas

    @property
    def drag_coefficient(self):
        """CircuitToPulse 'drag_coefficient' property.

        Returns:
            float: settings.drag_coefficient.
        """
        return self.settings.drag_coefficient

    @property
    def gate_duration(self):
        """CircuitToPulse 'drag_duration' property.

        Returns:
            int: settings.gate_duration.
        """
        return self.settings.gate_duration

    @property
    def readout_pulse(self):
        """CircuitToPulse 'readout_pulse' property.

        Returns:
            ReadoutPulseSettings: settings.readout_pulse.
        """
        return self.settings.readout_pulse
