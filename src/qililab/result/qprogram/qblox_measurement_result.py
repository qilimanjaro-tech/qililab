# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""QbloxResult class."""
import numpy as np

from qililab.result.qprogram.measurement_result import MeasurementResult
from qililab.typings.enums import ResultName
from qililab.yaml import yaml


@yaml.register_class
class QbloxMeasurementResult(MeasurementResult):
    """QbloxQProgramMeasurementResult class. Contains the acquisitions results for a single measurement obtained from the `Cluster.get_acquisitions` method.

    The input to the constructor should be a dictionary with the following structure:

    - integration: integration data.
        - path_0: input path 0 integration result bin list.
        - path_1: input path 1 integration result bin list.
    - threshold: threshold result bin list.
    - valid: list of valid indications per bin.
    - avg_cnt: list of number of averages per bin.

    Args:
        raw_measurement_data (dict): Raw data obtained from the Qblox digitiser.
    """

    name = ResultName.QBLOX_QPROGRAM_MEASUREMENT

    def __init__(self, bus: str, raw_measurement_data: dict, shape: tuple | None = None):
        super().__init__(bus=bus)
        self.raw_measurement_data = raw_measurement_data
        self.shape = shape

    @property
    def array(self) -> np.ndarray:
        """Get I/Q data as an np.ndarray

        Returns:
            np.ndarray: The I/Q data
        """
        path0 = self.raw_measurement_data["bins"]["integration"]["path0"]
        path1 = self.raw_measurement_data["bins"]["integration"]["path1"]

        array = np.array([path0, path1])
        if self.shape:
            array = array.reshape((2, *self.shape))
        return array

    @property
    def threshold(self) -> np.ndarray:
        """Get the thresholded data as an np.ndarray.

        Returns:
            np.ndarray: The thresholded data.
        """
        array = np.array(self.raw_measurement_data["bins"]["threshold"])
        if self.shape:
            array = array.reshape((1, *self.shape))
        return array
