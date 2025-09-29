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
from copy import deepcopy

@yaml.register_class
class QbloxMeasurementResult(MeasurementResult):
    """QbloxMeasurementResult class. Contains the acquisitions results for a
    single measurement obtained from the `Cluster.get_acquisitions` method.

    This class stores the acquisition results from a single measurement
    obtained via the `Cluster.get_acquisitions` method. It parses and
    reshapes the raw data provided by the Qblox hardware into standardized
    numpy arrays for further processing.

    Args:
        name : ResultName
            Identifier for the type of result.
        raw_measurement_data : dict
            Raw dictionary of measurement data from the digitiser.
        shape : tuple of int or None
            Expected shape to reshape the raw measurement arrays into.
        bus : str
            Identifier for the acquisition bus.
    """

    name = ResultName.QBLOX_QPROGRAM_MEASUREMENT

    def __init__(self, bus: str, raw_measurement_data: dict, intertwined: int, shape: tuple | None = None):
        super().__init__(bus=bus)
        self.raw_measurement_data = raw_measurement_data
        self.shape = shape
        self.intertwined = intertwined


    @property
    def array(self) -> np.ndarray:
        """Get I/Q data as an np.ndarray

        Returns:
            np.ndarray: The I/Q data
        """
        path0 = self.raw_measurement_data["bins"]["integration"]["path0"]
        path1 = self.raw_measurement_data["bins"]["integration"]["path1"]

        array = np.array([path0, path1])

        # if self.intertwined > 1:
        #     array = [array[i::self.intertwined] for i in range(self.intertwined)]
        #     # array = [path1[i::self.intertwined] for i in range(self.intertwined)]

        if self.shape:
            array = array.reshape((2, *self.shape))
        #     if isinstance(array, list):
        #         array = [a.reshape((2, *self.shape)) for a in array]
        #     else:
                # array = array.reshape((2, *self.shape))
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
        if self.intertwined>1:
            pass
        return array

    @property
    def unintertwined(self) -> list:
        results_unintertwined_list = []
        if self.intertwined > 1:
            
            for i in range(self.intertwined):
                results_unintertwined: QbloxMeasurementResult = deepcopy(self)
                results_unintertwined.intertwined = 1
                # results_unintertwined.raw_measurement_data["scope"] = 
                path0 = results_unintertwined.raw_measurement_data["bins"]["integration"]["path0"]
                results_unintertwined.raw_measurement_data["bins"]["integration"]["path0"] = path0[i::self.intertwined]

                path1 = results_unintertwined.raw_measurement_data["bins"]["integration"]["path1"]
                results_unintertwined.raw_measurement_data["bins"]["integration"]["path1"] = path1[i::self.intertwined]

                threshold = results_unintertwined.raw_measurement_data["bins"]["threshold"]
                results_unintertwined.raw_measurement_data["bins"]["threshold"] = threshold[i::self.intertwined]

                avg_cnt = results_unintertwined.raw_measurement_data["bins"]["avg_cnt"]
                results_unintertwined.raw_measurement_data["bins"]["avg_cnt"] = avg_cnt[i::self.intertwined]

                results_unintertwined_list.append(results_unintertwined)

                # for result in range(self.intertwined):
                #     results_unintertwined.append(QbloxMeasurementResult(bus = self.bus, raw_measurement_data=split_raw_data, intertwined=1, shape=split_shape))
            
        else:
            results_unintertwined_list = [self]
            
        return results_unintertwined_list

