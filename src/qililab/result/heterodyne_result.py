"""Heterodyne Result class."""
from dataclasses import dataclass, field
from typing import List, Tuple

from qililab.constants import RUNCARD
from qililab.result.result import Result
from qililab.typings.enums import ResultName
from qililab.utils.factory import Factory


@Factory.register
@dataclass
class HeterodyneResult(Result):
    """Heterodyne Result class."""

    name: ResultName = ResultName.HETERODYNE
    integrated_i: list[float] = field(default_factory=list)
    integrated_q: list[float] = field(default_factory=list)

    def probabilities(self) -> List[Tuple[float, float]]:
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
        return {
            RUNCARD.NAME: self.name.value,
            "integrated_I": self.integrated_i,
            "integrated_Q": self.integrated_q,
        }
