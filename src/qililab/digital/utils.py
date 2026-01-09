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

from typing import Mapping

import numpy as np

from qililab.result.qprogram import QProgramResults


def qprogram_results_to_samples(
    qprogram_results: QProgramResults,
    logical_to_physical_qubits: Mapping[int, int],
    *,
    bus_fmt: str = "readout_q{idx}_bus",
    order: str = "q0-left",  # "q0-right" (Qiskit-like) or "q0-left"
    on_missing: str = "skip",  # "error", "zeros", or "skip"
) -> dict[str, int]:
    """
    Build a Samples dict (bitstring -> count) for the logical qubits.

    Args:
        logical_to_physical_qubits: dict mapping logical qubit index -> physical qubit index.
        bus_fmt: Format to locate each bus (default "readout_q{idx}_bus").
        order: Bitstring display order.
            "q0-right" => q0 is the least significant / rightmost bit.
            "q0-left" => q0 is the leftmost bit.
        on_missing:
            - "error": raise if a mapped physical qubit has no measurement.
            - "zeros": treat missing qubit as all-zeros (length inferred from other qubits).
            - "skip": drop missing qubits from the bitstrings.

    Returns:
        dict[str, int]: Samples mapping bitstring -> occurrences across shots.

    Raises:
        KeyError: missing measurement when on_missing="error".
        ValueError: inconsistent shot samples across qubits, or no data.
    """
    # Establish a stable logical-qubit order (0, 1, 2, ...)
    logicals: list[int] = sorted(logical_to_physical_qubits.keys())

    # Collect per-logical thresholds, ensuring same NSHOTS
    thresholds: dict[int, np.ndarray] = {}
    nshots: int | None = None
    missing_lqs: list[int] = []

    for lq in logicals:
        pq = logical_to_physical_qubits[lq]
        bus = bus_fmt.format(idx=pq)

        if bus not in qprogram_results.results or not qprogram_results.results[bus]:
            if on_missing == "error":
                raise KeyError(f"No measurement found for physical qubit {pq} (bus='{bus}').")
            missing_lqs.append(lq)
            continue

        arr = np.asarray(qprogram_results.results[bus][0].threshold).ravel().astype(np.uint8)
        if nshots is None:
            nshots = int(arr.size)
        elif arr.size != nshots:
            raise ValueError(
                f"Inconsistent number of shots: logical {lq} (physical {pq}) has {arr.size}, expected {nshots}."
            )
        thresholds[lq] = arr

    if nshots is None:
        raise ValueError("No measurement data found for any of the requested qubits.")

    # Handle missing qubits per policy
    if on_missing == "zeros":
        for lq in missing_lqs:
            thresholds[lq] = np.zeros(nshots, dtype=np.uint8)
    elif on_missing == "skip":
        logicals = [lq for lq in logicals if lq in thresholds]
        if not logicals:
            raise ValueError("All requested qubits were missing and were skipped; nothing to count.")

    # Build [NSHOTS, NLOG] matrix with columns ordered by logical qubit index
    shot_matrix = np.stack([thresholds[lq] for lq in logicals], axis=1)  # shape = (NSHOTS, NLOG)

    if order == "q0-right":
        weights = 1 << np.arange(shot_matrix.shape[1], dtype=np.uint64)
    else:
        weights = 1 << np.arange(shot_matrix.shape[1] - 1, -1, -1, dtype=np.uint64)

    codes = (shot_matrix.astype(np.uint64) * weights).sum(axis=1)
    unique_codes, counts = np.unique(codes, return_counts=True)
    w = shot_matrix.shape[1]
    return {format(code, f"0{w}b"): int(cnt) for code, cnt in zip(unique_codes.tolist(), counts.tolist())}
