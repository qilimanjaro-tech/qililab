""" Qblox Bins Acquisitions Result """

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import numpy.typing as npt
import pandas as pd

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
    pulse_length: int

    def __post_init__(self):
        """Create acquisitions"""
        self._acquisitions = [self._build_bin_acquisition(bin_data=bin_data) for bin_data in self.bins]

    def _build_bin_acquisition(self, bin_data: BinData):
        """build a bin acquisition"""
        i_values = np.array(bin_data.integration.path0, dtype=np.float32)
        q_values = np.array(bin_data.integration.path1, dtype=np.float32)
        return QbloxBinAcquisition(pulse_length=self.pulse_length, i_values=i_values, q_values=q_values)

    def probabilities(self) -> pd.DataFrame:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        acquisitions = self.acquisitions()
        probs_dict = {"acquisition_index": range(len(acquisitions)),
                      "p0": (self._get_last_bin(one_acquisition=acq)[2] for acq in acquisitions),
                      "p1": (self._get_last_bin(one_acquisition=acq)[2] for acq in acquisitions)}
        return pd.DataFrame(probs_dict)

    def _get_last_bin(self, one_acquisition: npt.NDArray[np.float32]) -> npt.NDArray:
        """get last bin"""
        # FIXME: Here we use -1 to get the last bin. Do we really want this?
        return one_acquisition[-1] if one_acquisition.ndim > 1 else one_acquisition
