""" Acquisitions Result """

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np
import numpy.typing as npt

from qililab.result.acquisition import Acquisition


@dataclass
class Acquisitions:
    """Acquisitions Results
    Args:
        acquisitions (List[Acquisition]): list of all the acquisition results

    """

    _acquisitions: List[Acquisition] = field(init=False)

    def acquisitions(self) -> npt.NDArray[np.float32]:
        """return the acquisitions with a structure
        I, Q, Amplitude, Phase
        """
        return np.array([acquisition.acquisition for acquisition in self._acquisitions])

    def probabilities(self) -> List[Tuple[float, float]]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        raise NotImplementedError
