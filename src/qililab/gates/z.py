from qibo import gates

from qililab.gates.abstract_gate import AbstractHardwareGate


class Z(AbstractHardwareGate, gates.Z):
    """Z gate"""

    def to_sequence(self, sequence: object) -> None:
        """Translates the gate to pulses and adds them to the given PulseSequence.

        Args:
            sequence (PulseSequence): Class containing the sequence of pulses to be applied.
        """
        raise NotImplementedError
