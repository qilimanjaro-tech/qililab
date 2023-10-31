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
class QuantumMachinesResult(Result):
    """QuantumMachinesResult class. Contains the binning acquisition results obtained from Quantum Machines Manager execute() method.

    Args:
        raw_results (list): Raw results obtained from a Quantum Machines Manager.
    """

    name = ResultName.QM

    def __init__(self, raw_results: list):
        self.raw_results = raw_results

    @property
    def array(self) -> np.ndarray:
        """Returns data as acquired from Quantum Machines Manager."""
        return np.array(self.raw_results)

    def to_dict(self) -> dict:
        """Returns a serialized dictionary of the QuantumMachinesResult class.

        Returns:
            dict[str: str | np.ndarray]: Dictionary containing all the class information.
        """
        return {
            RUNCARD.NAME: self.name.value,
            QMRESULT.QM_RAW_RESULTS: self.raw_results,
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
