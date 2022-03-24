from abc import ABC, abstractmethod

from qibo import gates

from qililab.config import raise_error

# TODO: Implement the gates declared below


class AbstractHardwareGate(ABC):
    """Abstract Base Class of a hardware gate."""

    # TODO: Replace 'object' with PulseSequence class
    @abstractmethod
    def to_sequence(self, sequence: object) -> None:
        """Translates the gate to pulses and adds them to the given PulseSequence.

        Args:
            sequence (PulseSequence): Class containing the sequence of pulses to be applied.
        """


# FIXME: Flake8 doesn't accept the 'I' class definition. Changed the name to Identity. Should we ignore this flake8 error?
class Identity(AbstractHardwareGate, gates.I):
    """Identity gate"""

    def to_sequence(self, sequence: object) -> None:
        """Translates the gate to pulses and adds them to the given PulseSequence.

        Args:
            sequence (PulseSequence): Class containing the sequence of pulses to be applied.
        """
        raise_error(NotImplementedError)


class X(AbstractHardwareGate, gates.I):
    """X gate"""

    def to_sequence(self, sequence: object) -> None:
        """Translates the gate to pulses and adds them to the given PulseSequence.

        Args:
            sequence (PulseSequence): Class containing the sequence of pulses to be applied.
        """
        raise_error(NotImplementedError)


class Y(AbstractHardwareGate, gates.I):
    """Y gate"""

    def to_sequence(self, sequence: object) -> None:
        """Translates the gate to pulses and adds them to the given PulseSequence.

        Args:
            sequence (PulseSequence): Class containing the sequence of pulses to be applied.
        """
        raise_error(NotImplementedError)


class Z(AbstractHardwareGate, gates.I):
    """Z gate"""

    def to_sequence(self, sequence: object) -> None:
        """Translates the gate to pulses and adds them to the given PulseSequence.

        Args:
            sequence (PulseSequence): Class containing the sequence of pulses to be applied.
        """
        raise_error(NotImplementedError)
