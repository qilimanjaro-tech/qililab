"""Class that translates a Qibo Circuit into a PulseSequence"""
from dataclasses import dataclass, field
from typing import Dict, List

from qibo.abstractions.gates import Gate
from qibo.core.circuit import Circuit

from qililab.chip import Chip
from qililab.pulse.hardware_gates import HardwareGateFactory
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_shape import Drag
from qililab.pulse.pulses import Pulses
from qililab.pulse.readout_pulse import ReadoutPulse
from qililab.settings import TranslationSettings


@dataclass
class CircuitToPulses:
    """Class that translates a Qibo Circuit into a PulseSequence"""

    settings: TranslationSettings

    def translate(self, circuits: List[Circuit], chip: Chip) -> List[Pulses]:
        """Translate a circuit into a pulse sequence.

        Args:
            circuit (Circuit): Qibo Circuit class.

        Returns:
            PulseSequences: Object containing the translated pulses.
        """
        pulses_list = []
        for circuit in circuits:
            time: Dict[int, int] = {}  # restart time
            control_gates = list(circuit.queue)
            readout_gate = circuit.measurement_gate
            pulses = [self._control_gate_to_pulse(time=time, control_gate=gate, chip=chip) for gate in control_gates]

            if readout_gate is not None:
                pulses.extend(
                    self._readout_gate_to_pulse(time=time, qubit_idx=qubit_idx, chip=chip)
                    for qubit_idx in readout_gate.target_qubits
                )

            pulses_list.append(Pulses(elements=pulses))

        return pulses_list

    def _control_gate_to_pulse(self, time: Dict[int, int], control_gate: Gate, chip: Chip) -> Pulse:
        """Translate a gate into a pulse.

        Args:
            gate (Gate): Qibo Gate.

        Returns:
            Pulse: Pulse object.
        """
        amplitude, phase = HardwareGateFactory.get(control_gate)
        if amplitude is None or phase is None:
            raise NotImplementedError(f"Qililab has not defined a gate {control_gate.__class__.__name__}")
        port = chip.get_port_from_qubit_idx(idx=control_gate.target_qubits[0], readout=False)
        old_time = self._update_time(
            time=time, port=port.id_, pulse_time=self.settings.gate_duration + self.settings.delay_between_pulses
        )
        return Pulse(
            amplitude=float(amplitude),
            phase=float(phase),
            duration=self.settings.gate_duration,
            port=port.id_,
            pulse_shape=Drag(num_sigmas=self.settings.num_sigmas, beta=self.settings.drag_coefficient),
            start_time=old_time,
        )

    def _readout_gate_to_pulse(self, time: Dict[int, int], qubit_idx: int, chip: Chip) -> ReadoutPulse:
        """Translate a gate into a pulse.

        Args:
            gate (Gate): Qibo Gate.

        Returns:
            Pulse: Pulse object.
        """
        port = chip.get_port_from_qubit_idx(idx=qubit_idx, readout=True)
        old_time = self._update_time(
            time=time, port=port.id_, pulse_time=self.settings.readout_duration + self.settings.delay_before_readout
        )
        return ReadoutPulse(
            amplitude=self.settings.readout_amplitude,
            phase=self.settings.readout_phase,
            duration=self.settings.readout_duration,
            port=port.id_,
            start_time=old_time,
        )

    def _update_time(self, time: Dict[int, int], port: int, pulse_time: int):
        """Create new timeline if not already created and update time.

        Args:
            port (int): Index of the chip port.
            pulse_time (int): Duration of the puls + wait time.
        """
        if port not in time:
            time[port] = 0
        old_time = time[port]
        time[port] += pulse_time
        return old_time
