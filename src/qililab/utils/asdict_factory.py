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

"""dict_factory used for dataclass' asdict method."""
from enum import Enum


def dict_factory(data):
    """dict factory used in the asdict() dataclass function. Replace all Enum classes by its corresponding values
    and all BusElement objects with its corresponding settings dictionaries."""
    result: dict[str, list[dict[str, int | float | str]] | str | int | float] = {}
    for key, value in data:
        if isinstance(value, Enum):
            value = str(value.value)
        result = result | {key: value}
    return result
