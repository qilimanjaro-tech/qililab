"""Result class."""
from dataclasses import asdict, dataclass, field
from typing import Tuple

from qililab.constants import YAML
from qililab.typings import FactoryElement, ResultName


# FIXME: Cannot use dataclass and ABC at the same time
@dataclass
class Result(FactoryElement):
    """Result class."""

    name: ResultName = field(init=False)

    def plot(self):
        """Plot results."""
        raise NotImplementedError

    def probabilities(self) -> Tuple[float, float]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        raise NotImplementedError

    def to_dict(self) -> dict:
        """
        Returns:
            dict: Dictionary containing all the class information.
        """
        return asdict(self) | {YAML.NAME: self.name.value}
