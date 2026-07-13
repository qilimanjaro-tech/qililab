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


def sort_buses(bus_sequence: Iterable[str]) -> list[str]:
    """It sorts buses on 4 criteria using RegEx:
        - The amount of ints (to separate couplers from qubit buses).
        - What ints appear ('drive_2 before drive_5').
        - What type of bus is it (readout > drive > flux > unspecified).
        - What qubit loop it connects to (x > z > unspecified).
        - Alphabetic sorting if everything else fails.

    Args:
        bus_sequence (Iterable[str]): List or tuple of bus identifiers.

    Returns:
        list[str]: Sorted list of bus identifiers.
    """
    loop_type_order = {"x": 1, "z": 2}
    bus_type_order = (
        (r"readout|(?<![a-z])(?:ro)(?![a-z])", 0),
        (r"drive|(?<![a-z])(?:d)(?![a-z])", 1),
        (r"flux|(?<![a-z])(?:f)(?![a-z])", 2),
    )

    def bus_sort_key(bus: str):
        ids = sorted(int(i) for i in re.findall(r"\d+", bus))
        bus_type = next((order for RE, order in bus_type_order if re.search(RE, bus, flags=re.IGNORECASE)), 3)
        loop_type = loop_type_order.get(
            m.group().lower() if (m := re.search(r"(?<!flu)[xz]", bus, flags=re.IGNORECASE)) else "", 3
        )
        return (len(ids), ids, bus_type, loop_type, bus)

    return sorted(bus_sequence, key=bus_sort_key)
