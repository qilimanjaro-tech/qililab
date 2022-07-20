"""QbloxResult class."""
from dataclasses import dataclass
from typing import List, Tuple

from qililab.result.result import Result
from qililab.typings.enums import ResultName
from qililab.utils.factory import Factory


@Factory.register
@dataclass
class SimulatorResult(Result):
    """SimulatorResult class."""

    name = ResultName.SIMULATOR

    prob_0: float
    prob_1: float

    def probabilities(self) -> List[Tuple[float, float]]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        return [(self.prob_0, self.prob_1)]

    def plot(self):
        """Plot data."""
        raise NotImplementedError
