"""Result class."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple


# FIXME: Cannot use dataclass and ABC at the same time
@dataclass
class Result:
    """Result class."""

    def plot(self):
        """Plot results."""
        raise NotImplementedError

    def probabilities(self) -> Tuple[float, float]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        raise NotImplementedError
