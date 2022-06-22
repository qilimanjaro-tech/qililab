"""QbloxResult class."""
from dataclasses import dataclass, field
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

    @dataclass
    class ScopeData:
        """Scope data."""

        @dataclass
        class PathData:
            """Path data."""

            data: List[float]
            avg_cnt: int
            out_of_range: bool

        path0: PathData
        path1: PathData

        def __post_init__(self):
            """Change invalid name and cast to PathData class."""
            if isinstance(self.path0, dict) and isinstance(self.path1, dict):
                self.path0["out_of_range"] = self.path0.pop("out-of-range")
                self.path0 = self.PathData(**self.path0)
                self.path1["out_of_range"] = self.path1.pop("out-of-range")
                self.path1 = self.PathData(**self.path1)

    scope: ScopeData | None = None
    bins: BinData | None = None
    shape: List[int] = field(init=False)

    def __post_init__(self):
        """Cast dictionaries to their corresponding class."""
        if self.scope is not None:
            self.shape = [16384, 2]
            self.scope = self.ScopeData(**self.scope)
        if self.bins is not None:
            self.shape = [4]
            self.bins = self.BinData(**self.bins)

    def acquisitions(self) -> Tuple[float, float, float, float] | np.ndarray:
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
            return np.array([self.scope.path0.data, self.scope.path1.data]).transpose()

        raise ValueError("There is no data stored.")

    def probabilities(self):
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        # TODO:: Measure real probabilities from calibrated max and min amplitude values.
        if self.bins is not None:
            return self.acquisitions()[2], self.acquisitions()[2]
        if self.scope is not None:  # TODO: Integrate data when scope is not None.
            return self.acquisitions()[0][-1], self.acquisitions()[-1]

    def plot(self):
        """Plot data."""
        raise NotImplementedError
