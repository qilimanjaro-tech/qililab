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
    integrated_I: float = 0.0
    integrated_Q: float = 0.0

    def probabilities(self) -> List[Tuple[float, float]]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        return [(20 * np.log10(np.sqrt(self.integrated_I**2 + self.integrated_Q**2)), 0.0)]

    def to_dict(self) -> dict:
        """
        Returns:
            dict: Dictionary containing all the class information.
        """
        return {
            RUNCARD.NAME: self.name.value,
            "integrated_I": float(self.integrated_I),
            "integrated_Q": float(self.integrated_Q),
        }
