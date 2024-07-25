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

"""QuantumMachinesResult class."""
import numpy as np

from qililab.result.qprogram.measurement_result import MeasurementResult
from qililab.typings.enums import ResultName
from qililab.yaml import yaml


@yaml.register_class
class QuantumMachinesMeasurementResult(MeasurementResult):
    """Contains the data obtained from a single measurment in Quantum Machines hardware.

    Args:
        I (np.ndarray): Data obtained from I stream.
        Q (np.ndarray): Data obtained from Q stream.
        adc1 (np.ndarray, Optional): Data obtained from adc1 stream. Defaults to None.
        adc2 (np.ndarray, Optional): Data obtained from adc2 stream. Defaults to None.
    """

    name = ResultName.QUANTUM_MACHINES_MEASUREMENT

    def __init__(
        self,
        I: np.ndarray,
        Q: np.ndarray,
        adc1: np.ndarray | None = None,
        adc2: np.ndarray | None = None,
        classification_th: float | None = None,
    ):
        self.I = I
        self.Q = Q
        self.adc1 = adc1
        self.adc2 = adc2
        self._classification_threshold = classification_th
        super().__init__()

    @property
    def array(self) -> np.ndarray:
        """Returns I/Q data as a combined numpy array.

        Returns:
            np.ndarray: The I/Q data as a compined nummpy array.
        """

        return np.concatenate((self.I.reshape(1, *self.I.shape), self.Q.reshape(1, *self.Q.shape)), axis=0)

    @property
    def threshold(self) -> np.ndarray:
        """Get the thresholded data as an np.ndarray.

        Returns:
            np.ndarray: The thresholded data.
        """

        return (
            np.where(self.I >= self._classification_threshold, 1.0, 0.0)
            if self._classification_threshold is not None
            else np.zeros(self.I.shape)
        )
