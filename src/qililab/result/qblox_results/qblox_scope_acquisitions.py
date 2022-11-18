""" Qblox Scope Acquisitions Result """

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd

from qililab.constants import RESULTSDATAFRAME
from qililab.result.acquisition import Acquisition
from qililab.result.acquisitions import Acquisitions
from qililab.result.qblox_results.scope_data import ScopeData


@dataclass
class QbloxScopeAcquisitions(Acquisitions):
    """Qblox Scope Acquisitions Result
    Args:
        scope: ScopeData
        pulse_length (int): Duration (in ns) of the pulse

    """

    scope: ScopeData
    pulse_length: int

    def __post_init__(self):
        """Create acquisitions"""
        i_values = np.array(self.scope.path0.data, dtype=np.float32)
        q_values = np.array(self.scope.path1.data, dtype=np.float32)

        self._acquisitions = [Acquisition(pulse_length=self.pulse_length, i_values=i_values, q_values=q_values)]
        self.data_dataframe_indices = set().union(*[acq.data_dataframe_indices for acq in self._acquisitions])

    def probabilities(self) -> pd.DataFrame:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        acquisitions = self.acquisitions()
        probs_df = pd.DataFrame()
        probs_df[RESULTSDATAFRAME.P0] = acquisitions[RESULTSDATAFRAME.AMPLITUDE].values
        probs_df[RESULTSDATAFRAME.P1] = acquisitions[RESULTSDATAFRAME.AMPLITUDE].values
        probs_df.index.rename(RESULTSDATAFRAME.ACQUISITION_INDEX, inplace=True)
        return probs_df.iloc[-1:]
