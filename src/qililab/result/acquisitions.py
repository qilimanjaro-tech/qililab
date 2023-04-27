""" Acquisitions Result """

from dataclasses import dataclass, field

import pandas as pd

from qililab.constants import RESULTSDATAFRAME
from qililab.result.acquisition import Acquisition
from qililab.utils.dataframe_manipulation import concatenate_creating_new_name_index


@dataclass
class Acquisitions:
    """Acquisitions Results
    Args:
        acquisitions (list[Acquisition]): list of all the acquisition results

    """

    _acquisitions: list[Acquisition] = field(init=False)
    data_dataframe_indices: set[str] = field(init=False, default_factory=set)

    def acquisitions(self) -> pd.DataFrame:
        """return the acquisitions with a structure
        I, Q, Amplitude, Phase
        """
        acquisition_list = [acquisition.acquisition for acquisition in self._acquisitions]

        return concatenate_creating_new_name_index(
            dataframe_list=acquisition_list, new_index_name=RESULTSDATAFRAME.ACQUISITION_INDEX
        )

    def probabilities(self) -> pd.DataFrame:
        """Return probabilities of being in the ground and excited state.

        Returns:
            tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        raise NotImplementedError
