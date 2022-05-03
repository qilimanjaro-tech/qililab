"""QbloxResult class."""
from dataclasses import dataclass
from typing import List

from qililab.result.result import Result
from qililab.utils import nested_dataclass


# TODO: Here you probably can see my excitemenmt when using nested classes! XD
# I can perfectly understand that this structure may be overwhelming, but it's the best
# approach I found. Given that we receive a nested dictionary from Qblox, it's nice to have
# a dataclass for each dicionary inside the main dict. Given that these extra classes (QbloxAcquisitionData, ...)
# will ONLY be used by the QbloxResult class, I added them inside the class.
@nested_dataclass
class QbloxResult(Result):
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

        @nested_dataclass
        class QbloxScopeData:
            """QbloxScopeData class."""

            @dataclass
            class QbloxPathData:
                """QbloxPathData class."""

                data: list
                out_of_range: bool
                avg_cnt: int

            path0: QbloxPathData
            path1: QbloxPathData

        @nested_dataclass
        class QbloxBinData:
            """QbloxBinData class."""

            @dataclass
            class QbloxIntegrationData:
                """QbloxIntegrationData class."""

                path_0: List
                path_1: List

            integration: QbloxIntegrationData
            threshold: list
            valid: list
            avg_cnt: list

        scope: QbloxScopeData
        bins: QbloxBinData

    name: str
    index: int
    acquisition: QbloxAcquisitionData

    def plot(self):
        """Plot data."""
        raise NotImplementedError
