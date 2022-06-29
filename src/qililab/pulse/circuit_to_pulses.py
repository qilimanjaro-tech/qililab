"""Class that translates a Qibo Circuit into a PulseSequence"""
from dataclasses import dataclass

from qibo.abstractions.gates import Gate
from qibo.core.circuit import Circuit

from qililab.chip import Chip
from qililab.pulse.hardware_gates import HardwareGateFactory
from qililab.pulse.pulse import Pulse
from qililab.pulse.pulse_sequences import PulseSequences
from qililab.pulse.pulse_shape import Drag
from qililab.pulse.readout_pulse import ReadoutPulse
from qililab.settings import TranslationSettings


@dataclass
class CircuitToPulses:
    """Class that translates a Qibo Circuit into a PulseSequence"""

    def translate(self, circuit: Circuit, translation_settings: TranslationSettings, chip: Chip) -> PulseSequences:
        """Translate a circuit into a pulse sequence.

        Args:
            circuit (Circuit): Qibo Circuit class.

        Returns:
            PulseSequences: Object containing the translated pulses.
        """
        sequence = PulseSequences(
            delay_between_pulses=translation_settings.delay_between_pulses,
            delay_before_readout=translation_settings.delay_before_readout,
        )
        control_gates = list(circuit.queue)
        readout_gates = circuit.measurement_gate

        for gate in control_gates:
            sequence.add(self._gate_to_pulse(gate=gate, translation_settings=translation_settings, chip=chip))

        if readout_gates is not None:
            for qubit_id in circuit.measurement_gate.target_qubits:
                sequence.add(
                    ReadoutPulse(
                        amplitude=translation_settings.readout_amplitude,
                        phase=translation_settings.readout_phase,
                        duration=translation_settings.readout_duration,
                        port=chip.get_port_from_qubit_idx(idx=qubit_id, readout=True),
                    )
                )
        return sequence

    def _gate_to_pulse(self, gate: Gate, translation_settings: TranslationSettings, chip: Chip):
        """Translate a gate into a pulse.

        Args:
            gate (Gate): Qibo Gate.

        Returns:
            Pulse: Pulse object.
        """
        amplitude, phase = HardwareGateFactory.get(gate)
        if amplitude is None or phase is None:
            raise NotImplementedError(f"Qililab has not defined a gate {gate.__class__.__name__}")

        return Pulse(
            amplitude=float(amplitude),
            phase=float(phase),
            duration=translation_settings.gate_duration,
            port=chip.get_port_from_qubit_idx(
                idx=gate.target_qubits[0], readout=False
            ),  # FIXME: Create pulses for 2-qubit gates
            pulse_shape=Drag(num_sigmas=translation_settings.num_sigmas, beta=translation_settings.drag_coefficient),
        )
