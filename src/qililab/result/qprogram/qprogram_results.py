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
from itertools import product

import numpy as np

from qililab.result.counts import Counts
from qililab.result.qprogram.measurement_result import MeasurementResult
from qililab.yaml import yaml


# pylint: disable=too-few-public-methods
@yaml.register_class
class QProgramResults:
    """Results from a single execution of QProgram."""

    def __init__(self) -> None:
        self.results: dict[str, list[MeasurementResult]] = {}

    def append_result(self, bus: str, result: MeasurementResult):
        """Append a measurement result to bus's results list.

        Args:
            bus (str): The bus alias
            result (MeasurementResult): The measurement result to append.
        """
        if bus not in self.results:
            self.results[bus] = []
        self.results[bus].append(result)

    def _is_hw_avg_results(self) -> bool:
        """Returns if the current results dictionary has the format of results obtained with a HW higher than 1.

        Raises:
            ValueError: When not all the mesurements have the same HW average value
        """
        # Check all buses single results
        if all(len(result) == 1 for result in self.results.values()):
            # Check all buses same HW average
            hw_avg = self.results[next(iter(self.results))][0].hw_average
            if not all(result[0].hw_average == hw_avg for result in self.results.values()):
                raise ValueError(
                    f"Inconsistent hardware average count for different results, expected HW average of {hw_avg} on all results"
                )
            return True if hw_avg != 1 else False
        return False

    def probabilities(self) -> dict[str, float]:
        """Return probabilities of the quantum states.

        Raises:
            ValueError: When the `results` attribute is an empty dictionary

        Returns:
            dict[str, float]: Dictionary containing the quantum states as the keys of the dictionary, and the
                probabilities obtained for each state as the values of the dictionary.
        """
        if not self.results:
            raise ValueError(f"Can not obtain probabilities with no measurments, {self.__class__} empty")

        if self._is_hw_avg_results():
            return self._compute_hw_average_probabilities()

        return self.counts_object().probabilities()

    def _compute_hw_average_probabilities(self) -> dict[str, float]:
        """Return probabilities of the quantum states, obtained from results that were already averagd in hardware.
        The states preserve the same order of readout buses specification in the runcard,
        this means that if the runcard specifies readout buses ordered from qubit 0 to qubit n, then the sate '01' corresponds
        to the state where qubit 0 is measured in the ground state and qubit 1 is measured in the excited state.

        Returns:
            dict[str, float]: Dictionary containing the quantum states as the keys of the dictionary, and the
                probabilities obtained for each state as the values of the dictionary.
        """
        single_qb_prob = np.concatenate([result[0].threshold for result in self.results.values()])
        states = np.array(list(product([0, 1], repeat=len(single_qb_prob))))

        prob_matrix = np.where(states == 1, single_qb_prob, 1 - single_qb_prob)
        state_probs = np.prod(prob_matrix, axis=1)

        probabilities = {}
        for state, prob in zip(states, state_probs):
            if prob != 0:
                binary_state_str = "".join(state.astype(str))
                probabilities[binary_state_str] = prob
        return probabilities

    def counts(self):
        """Returns the counts dictionary containing the number of measurements (counts) of each state.

        Returns:
            dict[str, int]: Dictionary containing the number of measurements (value) in each state (key).
        """
        return self.counts_object().as_dict()

    def counts_object(self) -> Counts:
        """Returns a Counts object containing the amount of times each state was measured.

        Raises:
            ValueError: When results have a HW average different from 1.

        Returns:
            Counts: Counts object containing the amount of times each state was measured.
        """
        if self._is_hw_avg_results():
            raise ValueError(
                f"Can not obtain {Counts.__name__} of the measurements. Results were obtained with HW averaging, only probability is computable"
            )

        counts_object = Counts(n_qubits=len(self.results))
        # Build Matrix thresholds by ro bus
        # The threshold inside of a qblox bin is the name they use for already classified data as a value between
        # 0 and 1, not the value used in the comparator to perform such classification.
        th_matrix = np.array(
            [np.concatenate([measurement.threshold for measurement in result]) for result in self.results.values()]
        )
        # Transpose it and and concat by rows
        th_matrix_T = th_matrix.transpose()
        # Iterate and add each collapsed row (now state) into Counter
        for state in th_matrix_T:
            binary_state_str = "".join(state.astype(str))
            counts_object.add_measurement(state=binary_state_str)
        return counts_object
