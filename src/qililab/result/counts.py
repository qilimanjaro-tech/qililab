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

from __future__ import annotations

from collections import Counter
from typing import Counter as TCounter

import numpy as np


class Counts:
    """
    Class representing the number of times (counts) each state was measured.
    """

    def __init__(self, n_qubits: int):
        self.n_qubits = n_qubits
        n_states = 2**self.n_qubits if self.n_qubits > 0 else 0
        # Initialize counter with all n-qubits basis elements as keys and 0 as values.
        self._counter = Counter({bin(i)[2:].zfill(self.n_qubits): 0 for i in range(n_states)})
        self._total_measurements = 0

    @property
    def counter(self) -> TCounter[str]:
        """Counter object holding the counts.

        Returns:
            collections.Counter[str]: Counter object holding the counts.
        """
        return self._counter

    def as_dict(self) -> dict[str, int]:
        """Dictionary representation of the Counts object

        Returns:
            dict[str, int]: Dictionary containing the number of measurements (value) at each state (key).
        """
        return dict(self._counter)

    @property
    def total_measurements(self) -> int:
        """Number of total measurements held by the Counts object.

        Returns:
            int: number of measurements at all the states.
        """
        return self._total_measurements

    def add_measurement(self, state: str):
        """Adds a measurement to the Counts object.

        Args:
            state (str): string with 0s and 1s representing the state to add to the Count.
        """
        self._verify_state(state)
        self._counter.update([state])
        self._total_measurements += 1

    def add_counts(self, counts: Counts):
        """Adds all the counts from another Counts object to this Counts object.

        Args:
            counts (Counts): Counts object to add.

        Raises:
            IndexError: Received a counts object with a different number of qubits.
        """
        if self.n_qubits != counts.n_qubits:
            raise IndexError(
                f"Counts object with {counts.n_qubits} can't be added to Counts object with {self.n_qubits} qubits."
            )
        self._counter.update(counts.counter)
        self._total_measurements += counts.total_measurements

    def probabilities(self) -> dict[str, float]:
        """Returns the probabilities of each measurement.

        Returns:
            dict[str, float]: Dictionary of probabilities (value) of each measurement (key).
        """
        return {measurement: counts / self._total_measurements for (measurement, counts) in self._counter.items()}

    def _verify_state(self, state: str) -> None:
        """Verifies that a state is valid for the Counts object.

        Args:
            state (str): string with 0s and 1s representing the state to add to the Count.

        Raises:
            IndexError: Received a state representing a number of qubits different from the number of qubits of the Counts object.
            ValueError: Received a state made of elements other than 0s and 1s.
        """
        if len(state) != self.n_qubits:
            raise IndexError(f"State '{state}' can't be added to Counts object with {self.n_qubits} qubits.")
        if any(bit not in ["0", "1"] for bit in state):
            raise ValueError(f"A state can only be made of 0s and 1s, got state '{state}'.")

    def __str__(self) -> str:
        """String representation of the Counts object.

        Returns:
            str: String representation of the Counts object.
        """
        return str(self.as_dict())

    def __iadd__(self, other: Counts) -> Counts:
        """In-place addition of two Counts objects (self += other). Adds the `other` Counts object to itself.

        Args:
            other (Counts): Counts object to add to this Counts object.

        Returns:
            Counts: Reference to self.
        """
        self.add_counts(other)
        return self

    @staticmethod
    def from_qprogram(qprogram_results, qubit_mapping: list[str] | None = None):
        """Returns `Count` object from a `QProgramResults`.

        Args:
            qprogram_results (QProgramResults): The QProgramResults object we want to get the `Counts` from.
            qubit_mapping (list[str], optional): A list containing the names of the buses to map.
                Each bus is mapped to a qubit at the corresponding index; the bus at the i-th position in the list is mapped to the i-th qubit.
                Defaults to None.

        Raises:
           ValueError: If the `results` attribute of `qprogram_results` is an empty dictionary.
            ValueError: If the qubit mapping is incomplete and does not map all qubits.
            ValueError: If a qubit mapping is specified and any of the buses do not match the ones in the runcard.

        Returns:
            dict[str, float]: A dictionary where the keys are the quantum states, and the values are the probabilities obtained for each state.
        """
        if not qprogram_results.results:
            raise ValueError(f"Can not obtain counts with no measurments, {qprogram_results.__class__} empty")

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
        threshold_matrix = np.array(
            [
                np.concatenate([measurement.threshold.astype(int) for measurement in qprogram_results.results[bus]])
                for bus in buses
            ]
        )
        threshold_matrix_T = threshold_matrix.transpose()
        for state in threshold_matrix_T:
            binary_state_str = "".join(state.astype(str))
            counts_object.add_measurement(state=binary_state_str)

        return counts_object
