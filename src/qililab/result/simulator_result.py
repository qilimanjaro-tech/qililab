"""QbloxResult class."""
from dataclasses import dataclass

from qililab.result.result import Result


@dataclass
class SimulatorResult(Result):
    """SimulatorResult class."""

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
