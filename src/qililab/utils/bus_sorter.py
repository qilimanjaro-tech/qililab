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

import re
from typing import Iterable

_LOOP_TYPE_ORDER = {"x": 1, "z": 2}
_BUS_TYPE_ORDER = (
    (r"readout|(?<![a-z])(?:ro)(?![a-z])", 0),
    (r"drive|(?<![a-z])(?:d)(?![a-z])", 1),
    (r"flux|(?<![a-z])(?:f)(?![a-z])", 2),
)


def _bus_sort_key(bus: str):
    """Sort key for a single bus name. See :func:`sort_buses` for the ordering criteria."""
    ids = sorted(int(i) for i in re.findall(r"\d+", bus))
    bus_type = next((order for pattern, order in _BUS_TYPE_ORDER if re.search(pattern, bus, flags=re.IGNORECASE)), 3)
    loop_type = _LOOP_TYPE_ORDER.get(
        m.group().lower() if (m := re.search(r"(?<![a-z])[xz](?![a-z])", bus, flags=re.IGNORECASE)) else "", 3
    )
    return (len(ids), ids, bus_type, loop_type, bus)


def argsort_buses(bus_sequence: Iterable[str]) -> tuple[list[str], list[int]]:
    """Sort buses like :func:`sort_buses`, additionally returning the index permutation.

    Args:
        bus_sequence (Iterable[str]): Bus identifiers to sort.

    Returns:
        tuple[list[str], list[int]]: (sorted_buses, order) where
            sorted_buses[k] == list(bus_sequence)[order[k]].
    """
    items = list(bus_sequence)
    order = sorted(range(len(items)), key=lambda i: _bus_sort_key(items[i]))
    return [items[i] for i in order], order


def sort_buses(bus_sequence: Iterable[str]) -> list[str]:
    """Sort bus identifiers into a stable, easy to read order.

    The sorting criteria by order of importance are:

    1. Count of integers in the name — single-index qubit buses (one number) sort
       before two-index couplers, e.g. "flux q9" before "coupler 0 1".
    2. The integers themselves, compared numerically — so "drive q2" sorts before
       "drive q10" (plain alphabetical order would put q10 first).
    3. Bus type: readout < drive < flux < unspecified.
    4. Loop type: x < z < unspecified (x and z are only identified if there are no surrounding letters).
    5. The raw string, as a final alphabetical tiebreak for full determinism.

    Args:
        bus_sequence (Iterable[str]): Bus identifiers to sort.

    Returns:
        list[str]: The identifiers sorted by the criteria above.
    """
    return argsort_buses(bus_sequence)[0]
