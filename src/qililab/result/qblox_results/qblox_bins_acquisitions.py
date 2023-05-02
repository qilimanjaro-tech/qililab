""" Qblox Bins Acquisitions Result """

from collections import Counter
from dataclasses import dataclass
from typing import Counter as TCounter
from typing import List, Tuple

import numpy as np
import pandas as pd

from qililab.constants import RESULTSDATAFRAME
from qililab.result.acquisitions import Acquisitions
from qililab.result.counts import Counts
from qililab.result.qblox_results.bins_data import BinsData
from qililab.result.qblox_results.qblox_bins_acquisition import QbloxBinAcquisition


@dataclass
class QbloxBinsAcquisitions(Acquisitions):
    """Qblox Bins Acquisitions Results
    Args:
        bins (list[BinsData]): List containing a BinsData for each sequencer.
        integration_lengths (list[int]): List of integration lengths for each sequencer.
    """

    bins: List[BinsData]
    integration_lengths: list[int]

    def __post_init__(self):
        """Create acquisitions"""
        self._acquisitions = [
            self._build_bin_acquisition(bins_data=bins_data, integration_length=self.integration_lengths[sequencer_id])
            for sequencer_id, bins_data in enumerate(self.bins)
        ]
        self.data_dataframe_indices = set().union(*[acq.data_dataframe_indices for acq in self._acquisitions])

    def _build_bin_acquisition(self, bins_data: BinsData, integration_length: int):
        """build a bin acquisition"""
        i_values = np.array(bins_data.integration.path0, dtype=np.float32)
        q_values = np.array(bins_data.integration.path1, dtype=np.float32)
        return QbloxBinAcquisition(integration_length=integration_length, i_values=i_values, q_values=q_values)

    def counts(self) -> Counts:
        """Return the counts of measurements in each state.

        Returns:
            Counter[str]: Counter with the number of measurements in that state.
        """
        # TODO: Assuming that all sequencers are used for multiplexed readout then having the same number of bins, where each index corresponds to a simultaneous measurement with a different sequencer.
        # Check that all sequencers have the same number of bins.
        if any(len(seq_bins) != (num_bins := len(self.bins[0])) for seq_bins in self.bins):
            raise IndexError("Sequencers must have the same number of bins.")
        # TODO: Add limitations to check we are doing single-shot for multi qubit?
        counts_object = Counts(n_qubits=len(self.bins))
        for bin_idx in range(num_bins):
            measurement_as_list = [int(bins_data.threshold[bin_idx]) for bins_data in self.bins]
            measurement = "".join(str(bit) for bit in measurement_as_list)
            counts_object.add_measurement(state=measurement)
        return counts_object
