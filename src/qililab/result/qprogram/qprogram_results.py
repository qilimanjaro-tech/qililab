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


def probabilities(qprogram_results: QProgramResults, qubit_mapping: list[str] | None = None) -> dict[str, float]:
    """Return probabilities of the quantum states.

    Args:
        qprogram_results (QProgramResults): The QProgramResults object we want to get the probabilities from.
        qubit_mapping (list[str], optional): A list containing the name of the busses to map.
            The buses are map to qubits on the same index, a bus at the i-th element in the list is mapped to the i-th qubit.
            Defaults to None.

    Raises:
        ValueError: When the `results` attribute from `qprogram_results` is an empty dictionary.
        ValueError: When a qubit mapping is incomplete and does not map all qubits.
        ValueError: When a qubit mapping is specified and any of the busses does not match with any on the runcard.

    Returns:
        dict[str, float]: Dictionary containing the quantum states as the keys of the dictionary, and the
            probabilities obtained for each state as the values of the dictionary.
    """
    if not qprogram_results.results:
        raise ValueError(f"Can not obtain probabilities with no measurments, {qprogram_results.__class__} empty")

    n_qubits = len(qprogram_results.results)
    counts_object = Counts(n_qubits)
    buses = list(qprogram_results.results.keys())

    if qubit_mapping is not None:
        unique_mapping = set(qubit_mapping)  # Remove possible repeated elements
        if n_qubits != len(unique_mapping):
            raise ValueError(
                f"Expected mapping for all qubits. Results have {n_qubits} qubits, but only {len(unique_mapping)} diferent buses were specified on the mapping."
            )
        if not unique_mapping.issubset(set(buses)):
            raise ValueError(
                "No measurements found for all specified buses, check the name of the buses provided with the mapping match all the buses specified in runcard."
            )
        buses = qubit_mapping

    # The threshold inside of a qblox bin is the name they use for already classified data as a value between
    # 0 and 1, not the value used in the comparator to perform such classification.
    th_matrix = np.array(
        [[int(measurement.threshold) for measurement in qprogram_results.results[bus]] for bus in buses]
    )
    th_matrix_T = th_matrix.transpose()
    for state in th_matrix_T:
        binary_state_str = "".join(state.astype(str))
        counts_object.add_measurement(state=binary_state_str)

    return counts_object.probabilities()
