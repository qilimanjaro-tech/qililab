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

from warnings import warn

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
        adc1 (np.ndarray, optional): Data obtained from adc1 stream. Defaults to None.
        adc2 (np.ndarray, optional): Data obtained from adc2 stream. Defaults to None.
    """

    name = ResultName.QUANTUM_MACHINES_MEASUREMENT

    def __init__(
        self,
        bus: str,
        I: np.ndarray,
        Q: np.ndarray,
        adc1: np.ndarray | None = None,
        adc2: np.ndarray | None = None,
    ):
        super().__init__(bus=bus)
        self.I = I
        self.Q = Q
        self.adc1 = adc1
        self.adc2 = adc2
        self._classification_threshold = None

    def set_classification_threshold(self, classification_threshold):
        """Sets the `_classification_threshold` of the class."""
        self._classification_threshold = classification_threshold

    @property
    def array(self) -> np.ndarray:
        """Returns I/Q data as a combined numpy array.

        Returns:
            np.ndarray: The I/Q data as a compined nummpy array.
        """

        return np.concatenate((self.I.reshape(1, *self.I.shape), self.Q.reshape(1, *self.Q.shape)), axis=0)

    @property
    def threshold(self) -> np.ndarray:
        """Get the thresholded data as an np.ndarray. If the threshold is `None` thus not specified, returns an array of zeros.

        Returns:
            np.ndarray: The thresholded data.
        """
        if self._classification_threshold is None:
            warn("Classification threshold is not specified, returning a `np.zeros` array.", stacklevel=2)

        return (
            np.where(self._classification_threshold <= self.I, 1.0, 0.0)
            if self._classification_threshold is not None
            else np.zeros(self.I.shape)
        )
