from qibo import gates

from qililab.config import raise_error
from qililab.gates.abstract_gate import AbstractHardwareGate


class Y(AbstractHardwareGate, gates.Y):
    """Y gate"""

    def to_sequence(self, sequence: object) -> None:
        """Translates the gate to pulses and adds them to the given PulseSequence.

        Args:
            sequence (PulseSequence): Class containing the sequence of pulses to be applied.
        """
        raise_error(NotImplementedError)
