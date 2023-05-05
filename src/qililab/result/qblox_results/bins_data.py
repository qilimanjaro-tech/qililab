""" Bin Data """
from dataclasses import dataclass
from typing import List

import numpy as np

from qililab.utils.nested_data_class import nested_dataclass


@nested_dataclass
class BinsData:
    """Holds the integrated and thresholded values of all bins in a sequencer."""

    @dataclass
    class QbloxIntegrationData:
        """QbloxIntegrationData class."""

        path0: List[float]
        path1: List[float]

        def __post_init__(self):
            """Remove nan values."""  # FIXME: Since we cannot do ascending loops in Qpysequence, we need to
            # use always a number of bins = num_loops + 1. Thus the first bin is always a nan.
            self.path0 = [value for value in self.path0 if not np.isnan(value)]
            self.path1 = [value for value in self.path1 if not np.isnan(value)]

    integration: QbloxIntegrationData
    threshold: list
    avg_cnt: list

    def __post_init__(self):
        """Remove nan values."""  # FIXME: Since we cannot do ascending loops in Qpysequence, we need to
        # use always a number of bins = num_loops + 1. Thus the first bin is always a nan.
        self.threshold = [value for value in self.threshold if not np.isnan(value)]
        self.avg_cnt = [value for value in self.avg_cnt if not np.isnan(value)]

    def __len__(self) -> int:
        """Returns the length of the QbloxIntegrationData, corresponding to the number of bins.

        Returns:
            int: Length of the QbloxIntegrationData.
        """
        return len(self.threshold)
