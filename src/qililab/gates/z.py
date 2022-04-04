from qibo import gates

from qililab.gates.hardware_gate import HardwareGate


class Z(HardwareGate, gates.Z):
    """Z gate"""

    def to_sequence(self, sequence: object) -> None:
        """Translates the gate to pulses and adds them to the given PulseSequence.

        Args:
            sequence (PulseSequence): Class containing the sequence of pulses to be applied.
        """
        raise NotImplementedError
