"""HardwardGate class."""
import sys
from abc import ABC, abstractmethod
from typing import Tuple


class HardwareGate(ABC):
    """Abstract Base Class of a hardware gate."""

    module = sys.modules[__name__]  # used to avoid maximum recursion depth with qibo gates

    @abstractmethod
    def amplitude_and_phase(self) -> Tuple[float, float]:
        """
        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
