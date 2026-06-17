# Copyright 2026 Qilimanjaro Quantum Tech
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
"""Utiliy class for hashing common classes."""

import hashlib

import numpy as np
from qpysequence import Sequence


def _hash_data_arrays(items: list) -> str:
    """Hash a list of ``Waveform``/``Weight`` dataclasses.

    The ``data`` payload is hashed from its raw numpy bytes (instead of its string representation) to avoid the cost of
    serializing potentially large arrays of floats. The ``name`` and ``index`` are folded in as well, since they define
    how each array is mapped inside the sequencer. Items are sorted by index so the hash is independent of insertion
    order.

    Args:
        items (list): list of ``Waveform`` or ``Weight`` dataclasses, each exposing ``index``, ``name`` and ``data``.

    Returns:
        str: hex digest of the combined hash.
    """
    hasher = hashlib.md5(usedforsecurity=False)
    for item in sorted(items, key=lambda item: item.index):
        hasher.update(item.name.encode("utf-8"))
        hasher.update(int(item.index).to_bytes(8, "little", signed=True))
        hasher.update(np.ascontiguousarray(item.data, dtype=np.float64).tobytes())
    return hasher.hexdigest()


def _hash_str(value: str) -> str:
    """Hash a string with MD5."""
    return hashlib.md5(value.encode("utf-8"), usedforsecurity=False).hexdigest()


def hash_qpy_sequence_components(sequence: Sequence) -> dict[str, str]:
    """Compute a per-component hash of a QPy Sequence.

    Hashes are computed independently for the ``program``, ``waveforms`` and ``weights`` so the caller can decide which
    parts of the sequence need to be re-uploaded. ``acquisitions`` are intentionally omitted: they are always
    re-uploaded, so hashing them would be wasted work.

    Args:
        sequence (Sequence): the QPy Sequence to hash.

    Returns:
        dict[str, str]: mapping of component name (``"program"``, ``"waveforms"``, ``"weights"``) to its hex digest.
    """
    return {
        "program": _hash_str(repr(sequence._program)),  # pylint: disable=protected-access
        "waveforms": _hash_data_arrays(sequence._waveforms._waveforms),  # pylint: disable=protected-access
        "weights": _hash_data_arrays(sequence._weights._weights),  # pylint: disable=protected-access
    }
