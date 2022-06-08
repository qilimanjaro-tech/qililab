"""QbloxResult class."""
from dataclasses import dataclass

from qililab.result.result import Result
from qililab.typings import ResultName
from qililab.utils import Factory


@Factory.register
@dataclass
class SimulatorResult(Result):
    """SimulatorResult class."""

    name = ResultName.SIMULATOR

    prob_0: float
    prob_1: float

    def probabilities(self):
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        return self.prob_0, self.prob_1

    def plot(self):
        """Plot data."""
        raise NotImplementedError
