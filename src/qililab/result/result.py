"""Result class."""
from abc import ABC, abstractmethod
from typing import Tuple


class Result(ABC):
    """Result class."""

    @abstractmethod
    def plot(self):
        """Plot results."""

    @abstractmethod
    def probabilities(self) -> Tuple[float, float]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
