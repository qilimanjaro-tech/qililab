from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Counter as TCounter


@dataclass
class Counts:
    """
    Class representing the number of times (counts) each state was measured.
    """

    n_qubits: int
    _counter: TCounter[str] = field(init=False)
    _total_measurements: int = field(init=False, default=0)

    def __post_init__(self):
        """Initialize the Counter object."""
        n_states = 2**self.n_qubits if self.n_qubits > 0 else 0
        self._counter = Counter({bin(i)[2:].zfill(self.n_qubits): 0 for i in range(n_states)})

    @property
    def counter(self) -> TCounter[str]:
        """Counter object holding the counts.

        Returns:
            collections.Counter[str]: Counter object holding the counts.
        """
        return self._counter

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
        self._counter += counts.counter
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
        return self._counter.__str__()

    def __iadd__(self, other: Counts) -> Counts:
        """In-place addition of two Counts objects (self += other). Adds the `other` Counts object to itself.

        Args:
            other (Counts): Counts object to add to this Counts object.

        Returns:
            Counts: Reference to self.
        """
        self.add_counts(other)
        return self
