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
"""Utiliy class for hashing common classes."""

import hashlib

from qpysequence import Sequence


def hash_qpy_sequence(sequence: Sequence):
    """Hash a QPy Sequence"""
    sequence_str = repr(sequence)
    return hashlib.md5(sequence_str.encode("utf-8"), usedforsecurity=False).hexdigest()
