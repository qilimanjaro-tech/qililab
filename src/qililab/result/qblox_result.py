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
    bins: List[BinData] | None = None

    def __post_init__(self):
        """Cast dictionaries to their corresponding class."""
        if self.scope is not None:
            self.scope = self.ScopeData(**self.scope)
        if self.bins is not None:
            self.bins = [self.BinData(**bin) for bin in self.bins]

    def acquisitions(self) -> np.ndarray:
        """Return acquisition values.

        Args:
            acquisition_name (str, optional): Name of the acquisition. Defaults to "single".

        Returns:
            Tuple[float]: I, Q, amplitude and phase.
        """
        if self.bins is not None:
            acquisitions = []
            for bin_data in self.bins:
                i_data = np.array(bin_data.integration.path0)
                q_data = np.array(bin_data.integration.path1)
                acquisitions.append(
                    np.array([i_data, q_data, np.sqrt(i_data**2 + q_data**2), np.arctan2(q_data, i_data)])
                    .transpose()
                    .squeeze()
                )
            return np.array(acquisitions)

        if self.scope is not None:
            return np.array([np.array([self.scope.path0.data, self.scope.path1.data]).transpose()])

        raise ValueError("There is no data stored.")

    def probabilities(self) -> List[Tuple[float, float]]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        # TODO:: Measure real probabilities from calibrated max and min amplitude values.
        probs: List[Tuple[float, float]] = []
        acquisitions = self.acquisitions()
        if self.bins is not None:
            for acq in acquisitions:
                if acq.ndim > 1:
                    acq = acq[-1]  # FIXME: Here we use -1 to get the last bin. Do we really want this?
                probs.append((acq[2], acq[2]))
        if self.scope is not None:  # TODO: Integrate data when scope is not None.
            probs.extend((acq[0][-1], acq[0][-1]) for acq in acquisitions)
        return probs

    def plot(self):
        """Plot data."""
        raise NotImplementedError

    @property
    def shape(self) -> List[int]:
        """QbloxResult 'shape' property.

        Returns:
            List[int]: Shape of the acquisitions.
        """
        return list(self.acquisitions().shape)
