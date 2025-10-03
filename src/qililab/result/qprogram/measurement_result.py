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

"""MeasurementResult class."""

from abc import ABC, abstractmethod

import numpy as np

from qililab.typings.enums import ResultName


class MeasurementResult(ABC):
    """Abstract base class for storing and accessing QProgram measurement
    results.

    This class defines the interface for a measurement result from the
    execution of a QProgram. It provides methods to access both the raw
    measured data and the thresholded (classified) version of that data.

    Subclasses must implement the `array` and `threshold` properties to define
    how raw and thresholded data are accessed or computed.

    Attributes:
        name (ResultName): Enum identifier for the result type.
        bus (str): Name of the readout bus associated with the result.
        shape (tuple | None): Optional shape of the result data. Used for
                              reshaping or validation.
    """

    name: ResultName

    def __init__(self, bus: str, shape: tuple | None = None):
        self.bus: str = bus
        self.shape = shape

    @property
    @abstractmethod
    def array(self) -> np.ndarray:
        """Returns the results in a numpy array format.

        Returns:
            np.ndarray: Numpy array containing the results.
        """

    @property
    @abstractmethod
    def threshold(self) -> np.ndarray:
        """Returns the thresholded data for the result.

        Returns:
            np.ndarray: Thresholded data for the result.
        """

