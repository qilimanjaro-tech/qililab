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

""" Utils for dictionaries manipulation """
import copy


def merge_dictionaries(origin: dict, new: dict) -> dict:
    """Recursively merge `new` into a copy of `origin` and returns the new dictionary."""
    merged = copy.deepcopy(origin)

    for key, value in new.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Recursively merge dictionaries
            merged[key] = merge_dictionaries(merged[key], value)
        else:
            merged[key] = value

    return merged
