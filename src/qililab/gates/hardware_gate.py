import sys
from abc import ABC, abstractmethod


class HardwareGate(ABC):
    """Abstract Base Class of a hardware gate."""

    module = sys.modules[__name__]  # used to avoid maximum recursion depth with qibo gates

    # TODO: Replace 'object' with PulseSequence class
    @abstractmethod
    def to_sequence(self, sequence: object) -> None:
        """Translates the gate to pulses and adds them to the given PulseSequence.

        Args:
            sequence (PulseSequence): Class containing the sequence of pulses to be applied.
        """
