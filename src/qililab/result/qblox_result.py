"""QbloxResult class."""
from dataclasses import dataclass, InitVar, field
from typing import List, Tuple

import numpy as np

from qililab.result.result import Result
from qililab.typings import AcquisitionName
from qililab.utils import nested_dataclass

@dataclass
class QbloxResult(Result):
    """QbloxResult class."""

    @nested_dataclass
    class QbloxAcquisitions:
        """QbloxResult class. Contains the acquisition results obtained from the `Pulsar.get_acquisitions` method.
        The input to the constructor should be a dictionary with the following structure:

        - name: acquisition name.
        - index: acquisition index used by the sequencer Q1ASM program to refer to the acquisition.
        - acquisition: acquisition dictionary.
            - scope: Scope data.
                -path0: input path 0.
                    - data: acquisition samples in a range of 1.0 to -1.0.
                    - out-of-range: out-of-range indication for the entire
                    acquisition (False=in-range, True=out-of-range).
                    - avg_cnt: number of averages.
                - path1: input path 1
                    - data: acquisition samples in a range of 1.0 to -1.0.
                    - out-of-range: out-of-range indication for the entire
                    acquisition (False=in-range, True=out-of-range).
                    - avg_cnt: number of averages.
            - bins: bin data.
                - integration: integration data.
                    - path_0: input path 0 integration result bin list.
                    - path_1: input path 1 integration result bin list.
                - threshold: threshold result bin list.
                - valid: list of valid indications per bin.
                - avg_cnt: list of number of averages per bin.
        """

        @nested_dataclass
        class QbloxAcquisitionData:
            """QbloxAcquisitionResult class."""

            @dataclass
            class QbloxScopeData:
                """QbloxScopeData class."""

                @dataclass
                class QbloxPathData:
                    """QbloxPathData class."""

                    data: list
                    out_of_range: bool
                    avg_cnt: int

                path0: QbloxPathData | dict
                path1: QbloxPathData | dict

                def __post_init__(self):
                    self.path0["out_of_range"] = self.path0.pop("out-of-range")
                    self.path1["out_of_range"] = self.path1.pop("out-of-range")
                    self.path0 = self.QbloxPathData(**self.path0)
                    self.path1 = self.QbloxPathData(**self.path1)

            @nested_dataclass
            class QbloxBinData:
                """QbloxBinData class."""

                @dataclass
                class QbloxIntegrationData:
                    """QbloxIntegrationData class."""

                    path0: List
                    path1: List

                integration: QbloxIntegrationData
                threshold: list
                avg_cnt: list

            scope: QbloxScopeData
            bins: QbloxBinData

        name: str
        index: int
        acquisition: QbloxAcquisitionData

    integration_length: int
    start_integrate: int
    result: InitVar[dict]
    results: List[QbloxAcquisitions] = field(init=False)

    def __post_init__(self, result: dict):
        self.results = [
            self.QbloxAcquisitions(**item | {"name": AcquisitionName(key).value}) for key, item in result.items()
        ]

    def acquisitions(self, acquisition_name: str = "single") -> Tuple[float, float, float, float]:
        """Return acquisition values.

        Args:
            acquisition_name (str, optional): Name of the acquisition. Defaults to "single".

        Returns:
            Tuple[float]: I, Q, amplitude and phase.
        """
        result = [res for res in self.results if AcquisitionName(res.name) == AcquisitionName(acquisition_name)][0]
        i_data = result.acquisition.bins.integration.path0[0]
        q_data = result.acquisition.bins.integration.path1[0]

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
