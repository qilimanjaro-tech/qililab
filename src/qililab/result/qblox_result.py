"""QbloxResult class."""
from dataclasses import dataclass
from typing import List

import numpy as np

from qililab.result.result import Result
from qililab.utils import nested_dataclass


# TODO: Here you probably can see my excitemenmt when using nested classes! XD
# I can perfectly understand that this structure may be overwhelming, but it's the best
# approach I found. Given that we receive a nested dictionary from Qblox, it's nice to have
# a dataclass for each dicionary inside the main dict. Given that these extra classes (QbloxAcquisitionData, ...)
# will ONLY be used by the QbloxResult class, I added them inside the class.
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

    def __init__(self, integration_length: int, start_integrate: int, result: dict):
        self.integration_length = integration_length
        self.start_integrate = start_integrate
        self.results = [self.QbloxAcquisitions(**item | {"name": key}) for key, item in result.items()]

    def voltages(self):
        """Return computed voltage.

        Returns:
            float: Voltage
        """
        voltages = []
        for result in self.results:
            integrated_i = result.acquisition.bins.integration.path0[0]
            integrated_q = result.acquisition.bins.integration.path1[0]
            voltages.append(np.sqrt(integrated_i**2 + integrated_q**2))

        return voltages

    def probabilities(self):
        """Return probabilities of being in the ground and excited state.

        Returns:
            Tuple[float, float]: Probabilities of being in the ground and excited state.
        """
        # FIXME: Compute probabilities
        return self.voltages(), self.voltages()

    def plot(self):
        """Plot data."""
        raise NotImplementedError
