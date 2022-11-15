""" Qblox Scope Acquisitions Result """

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd

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

    def probabilities(self) -> pd.DataFrame:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        acquisitions = self.acquisitions()
        probs_df = pd.DataFrame()
        probs_df["p0"] = acquisitions["amplitude_values"].values
        probs_df["p1"] = acquisitions["amplitude_values"].values
        probs_df.index.rename("acquisition_index", inplace=True)
        return probs_df
