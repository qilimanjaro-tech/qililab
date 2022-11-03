"""Heterodyne Result class."""
from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np

from qililab.constants import RUNCARD
from qililab.result.result import Result
from qililab.typings.enums import ResultName
from qililab.utils.factory import Factory


@Factory.register
@dataclass
class HeterodyneResult(Result):
    """Heterodyne Result class."""

    name: ResultName = ResultName.HETERODYNE
    integrated_i: float = 0.0
    integrated_q: float = 0.0

    def probabilities(self) -> List[Tuple[float, float]]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        return [(20 * np.log10(np.sqrt(self.integrated_i**2 + self.integrated_q**2)), 0.0)]

    def to_dict(self) -> dict:
        """
        Returns:
            dict: Dictionary containing all the class information.
        """
        return {
            RUNCARD.NAME: self.name.value,
            "integrated_I": float(self.integrated_i),
            "integrated_Q": float(self.integrated_q),
        }
