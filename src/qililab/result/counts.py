from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Counter as TCounter


@dataclass
class Counts:
    n_qubits: int
    _counter: TCounter[str] = field(init=False)
    _total_measurements: int = field(init=False)

    def __post_init__(self):
        n_states = 2**self.n_qubits if self.n_qubits > 0 else 0
        self._counter = Counter({bin(i)[2:].zfill(self.n_qubits): 0 for i in range(n_states)})
        self._total_measurements = 0

    def add_measurement(self, state: str):
        self._counter.update([state])
        self._total_measurements += 1

    def add_counts(self, counts: Counts):
        self._counter += counts._counter
        self._total_measurements += counts._total_measurements

    def probabilities(self) -> dict[str, float]:
        return {measurement: counts / self._total_measurements for (measurement, counts) in self._counter.items()}

    def __str__(self) -> str:
        return self._counter.__str__()

    def __iadd__(self, other: Counts):
        self.add_counts(other)
        return self
