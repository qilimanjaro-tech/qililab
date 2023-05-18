"""VNA Result class."""
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from qililab.result.counts import Counts
from qililab.result.result import Result
from qililab.typings.enums import ResultName
from qililab.utils.factory import Factory


@Factory.register
@dataclass
class VNAResult(Result):
    """VNAResult class."""

    name = ResultName.VECTOR_NETWORK_ANALYZER
    i: npt.NDArray[np.float32]
    q: npt.NDArray[np.float32]

    def acquisitions(self) -> tuple[np.ndarray, np.ndarray]:
        """Return acquisition values."""
        return self.i, self.q

    def counts(self) -> Counts:
        raise NotImplementedError
