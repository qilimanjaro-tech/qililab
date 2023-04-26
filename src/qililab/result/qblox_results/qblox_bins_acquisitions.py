""" Qblox Bins Acquisitions Result """

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd

from qililab.constants import RESULTSDATAFRAME
from qililab.result.acquisitions import Acquisitions
from qililab.result.qblox_results.bin_data import BinData
from qililab.result.qblox_results.qblox_bins_acquisition import QbloxBinAcquisition


@dataclass
class QbloxBinsAcquisitions(Acquisitions):
    """Qblox Bins Acquisitions Results
    Args:
        bins: List[BinData]
        pulse_length (int): Duration (in ns) of the pulse
    """

    bins: List[BinData]
    integration_lengths: list[int]

    def __post_init__(self):
        """Create acquisitions"""
        self._acquisitions = [
            self._build_bin_acquisition(bin_data=bin_data, integration_length=self.integration_lengths[sequencer_id])
            for sequencer_id, bin_data in enumerate(self.bins)
        ]
        self.data_dataframe_indices = set().union(*[acq.data_dataframe_indices for acq in self._acquisitions])

    def _build_bin_acquisition(self, bin_data: BinData, integration_length: int):
        """build a bin acquisition"""
        i_values = np.array(bin_data.integration.path0, dtype=np.float32)
        q_values = np.array(bin_data.integration.path1, dtype=np.float32)
        return QbloxBinAcquisition(integration_length=integration_length, i_values=i_values, q_values=q_values)

    def probabilities(self) -> pd.DataFrame:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        probs_df = pd.DataFrame()
        probabilities_1 = np.array([bin.threshold for bin in self.bins])
        probabilities_0 = 1.0 - probabilities_1
        probs_df[RESULTSDATAFRAME.P0] = probabilities_0
        probs_df[RESULTSDATAFRAME.P1] = probabilities_1
        probs_df.index.rename(RESULTSDATAFRAME.ACQUISITION_INDEX, inplace=True)
        return probs_df.iloc[-1:]
