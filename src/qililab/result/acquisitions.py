""" Acquisitions Result """

from dataclasses import dataclass, field
from typing import List, Tuple

import pandas as pd

from qililab.result.acquisition import Acquisition


@dataclass
class Acquisitions:
    """Acquisitions Results
    Args:
        acquisitions (List[Acquisition]): list of all the acquisition results

    """

    _acquisitions: List[Acquisition] = field(init=False)

    def acquisitions(self) -> pd.DataFrame:
        """return the acquisitions with a structure
        I, Q, Amplitude, Phase
        """
        acquisition_list = [acquisition.acquisition for acquisition in self._acquisitions]
        return pd.concat(acquisition_list, keys=range(len(acquisition_list)), names=['acquisition_index'])

    def probabilities(self) -> pd.DataFrame:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        raise NotImplementedError
