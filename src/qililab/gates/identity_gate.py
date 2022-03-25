from qibo import gates

from qililab.config import raise_error
from qililab.gates.abstract_gate import AbstractHardwareGate


# FIXME: Flake8 doesn't accept the 'I' class definition. Changed the name to Identity. Should we ignore this flake8 error?
class Identity(AbstractHardwareGate, gates.I):
    """Identity gate"""

    def to_sequence(self, sequence: object) -> None:
        """Translates the gate to pulses and adds them to the given PulseSequence.

        Args:
            sequence (PulseSequence): Class containing the sequence of pulses to be applied.
        """
        raise_error(NotImplementedError)
