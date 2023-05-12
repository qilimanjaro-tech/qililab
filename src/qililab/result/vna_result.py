"""VNA Result class."""
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import pandas as pd

from qililab.result.result import Result
from qililab.typings.enums import ResultName
from qililab.utils.factory import Factory


@Factory.register
@dataclass
class VNAResult(Result):
    """VNAResult class."""

    name = ResultName.VECTOR_NETWORK_ANALYZER
    data: npt.NDArray[np.float32]

    def acquisitions(self) -> np.ndarray:
        """Return acquisition values."""
        return self.data

    def probabilities(self) -> pd.DataFrame:
        """Return probabilities of being in the ground and excited state.

        Returns:
            tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        raise NotImplementedError
