"""QbloxResult class."""
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from qililab.result.result import Result
from qililab.typings import ResultName
from qililab.utils import Factory, nested_dataclass


@Factory.register
@dataclass
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

    @nested_dataclass
    class BinData:
        """Bin data."""

        @dataclass
        class QbloxIntegrationData:
            """QbloxIntegrationData class."""

            path0: List[float]
            path1: List[float]

        integration: QbloxIntegrationData
        threshold: list
        avg_cnt: list

    @nested_dataclass
    class ScopeData:
        """Scope data."""

        @dataclass
        class PathData:
            """Path data."""

            data: List[float]
            avg_cnt: int

        path0: PathData
        path1: PathData

    scope: ScopeData | None = None
    bins: BinData | None = None

    def __post_init__(self):
        """Cast dictionaries to their corresponding class."""
        if self.scope is not None:
            self.scope = self.ScopeData(**self.scope)
        if self.bins is not None:
            self.bins = self.BinData(**self.bins)

    def acquisitions(self) -> Tuple[float, float, float, float] | Tuple[List[float], List[float]]:
        """Return acquisition values.

        Args:
            acquisition_name (str, optional): Name of the acquisition. Defaults to "single".

        Returns:
            Tuple[float]: I, Q, amplitude and phase.
        """
        if self.bins is not None:
            i_data = self.bins.integration.path0[0]
            q_data = self.bins.integration.path1[0]

            return (
                i_data,
                q_data,
                np.sqrt(i_data**2 + q_data**2),
                np.arctan2(q_data, i_data),
            )
        if self.scope is not None:
            return self.scope.path0.data, self.scope.path1.data

        raise ValueError("There is no data stored.")

    def probabilities(self):
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        # TODO:: Measure real probabilities from calibrated max and min amplitude values.
        return self.acquisitions()[2], self.acquisitions()[2]

    def plot(self):
        """Plot data."""
        raise NotImplementedError
