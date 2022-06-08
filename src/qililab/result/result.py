"""Result class."""
from dataclasses import dataclass
from typing import Tuple

from qililab.typings import ResultName


# FIXME: Cannot use dataclass and ABC at the same time
@dataclass
class Result:
    """Result class."""

    name: ResultName

    def plot(self):
        """Plot results."""
        raise NotImplementedError

    def probabilities(self) -> Tuple[float, float]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        raise NotImplementedError
