"""QbloxResult class."""
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from qililab.result.result import Result
from qililab.utils import nested_dataclass, Factory
from qililab.typings import ResultName

@Factory.register
@nested_dataclass
class QbloxResult(Result):
    """QbloxResult class. Contains the binning acquisition results obtained from the `Pulsar.get_acquisitions` method.
    The input to the constructor should be a dictionary with the following structure:

    - integration: integration data.
        - path_0: input path 0 integration result bin list.
        - path_1: input path 1 integration result bin list.
    - threshold: threshold result bin list.
    - valid: list of valid indications per bin.
    - avg_cnt: list of number of averages per bin.
    """

    name = ResultName.QBLOX

    @dataclass
    class QbloxIntegrationData:
        """QbloxIntegrationData class."""

        path0: List
        path1: List

    integration: QbloxIntegrationData
    threshold: list
    avg_cnt: list

    def acquisitions(self) -> Tuple[float, float, float, float]:
        """Return acquisition values.

        Args:
            acquisition_name (str, optional): Name of the acquisition. Defaults to "single".

        Returns:
            Tuple[float]: I, Q, amplitude and phase.
        """
        i_data = self.integration.path0[0]
        q_data = self.integration.path1[0]

        return (
            i_data,
            q_data,
            np.sqrt(i_data**2 + q_data**2),
            np.arctan2(q_data, i_data),
        )

    def probabilities(self):
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        return self.acquisitions()[2], self.acquisitions()[2]

    def plot(self):
        """Plot data."""
        raise NotImplementedError
