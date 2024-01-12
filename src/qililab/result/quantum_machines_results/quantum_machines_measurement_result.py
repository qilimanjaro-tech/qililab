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

from qililab.constants import QMRESULT, RUNCARD
from qililab.result.counts import Counts
from qililab.result.result import Result
from qililab.typings.enums import ResultName
from qililab.utils.factory import Factory


@Factory.register
class QuantumMachinesMeasurementResult(Result):
    """Contains the data obtained from a single measurment in Quantum Machines hardware.

    Args:
        I (np.ndarray): Data obtained from I stream.
        Q (np.ndarray, Optional): Data obtained from Q stream. Defaults to None.
        adc1 (np.ndarray, Optional): Data obtained from adc1 stream. Defaults to None.
        adc2 (np.ndarray, Optional): Data obtained from adc2 stream. Defaults to None.
    """

    name = ResultName.QUANTUM_MACHINES_MEASUREMENT

    def __init__(
        self, I: np.ndarray, Q: np.ndarray | None = None, adc1: np.ndarray | None = None, adc2: np.ndarray | None = None
    ):
        self.I = I
        self.Q = Q
        self.adc1 = adc1
        self.adc2 = adc2

    @property
    def array(self) -> np.ndarray:
        """Returns I/Q data as a combined numpy array.

        Returns:
            np.ndarray: The I/Q data as a compined nummpy array.
        """

        return (
            np.concatenate((self.I.reshape(1, *self.I.shape), self.Q.reshape(1, *self.Q.shape)), axis=0)
            if self.Q is not None
            else self.I.reshape(1, *self.I.shape)
        )

    def to_dict(self) -> dict:
        """Returns a serialized dictionary of the QuantumMachinesResult class.

        Returns:
            dict[str: str | np.ndarray]: Dictionary containing all the class information.
        """
        return {
            RUNCARD.NAME: self.name.value,
            QMRESULT.I: self.I,
            QMRESULT.Q: self.Q,
            QMRESULT.ADC1: self.adc1,
            QMRESULT.ADC2: self.adc2,
        }

    def probabilities(self) -> dict[str, float]:
        """Return probabilities of being in the ground and excited state.

        Returns:
            dict[str, float]: Dictionary containing the quantum states as the keys of the dictionary, and the
                probabilities obtained for each state as the values of the dictionary.
        """
        raise NotImplementedError("Probabilities are not yet supported for Quantum Machines instruments.")

    def counts_object(self) -> Counts:
        """Returns a Counts object containing the amount of times each state was measured.

        Raises:
            NotImplementedError: Not implemented.

        Returns:
            Counts: Counts object containing the amount of times each state was measured.
        """
        raise NotImplementedError("Counts are not yet supported for Quantum Machines instruments.")
