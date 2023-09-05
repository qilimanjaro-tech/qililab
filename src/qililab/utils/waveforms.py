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

"""Waveform class."""
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Waveforms:
    """Waveform class that containg the I and Q modulated waveforms."""

    i: np.ndarray = field(default_factory=lambda: np.array([]))
    q: np.ndarray = field(default_factory=lambda: np.array([]))  # pylint: disable=invalid-name

    def add(self, imod: np.ndarray, qmod: np.ndarray):
        """Add i and q arrays to the waveforms.

        Args:
            imod (np.ndarray): I modulated waveform to add.
            qmod (np.ndarray): Q modulated waveform to add.
        """
        self.i = np.append(self.i, imod)
        self.q = np.append(self.q, qmod)

    @property
    def values(self):
        """Return the waveform i and q values.

        Returns:
            np.ndarray: Array containing the i and q waveform values.
        """
        return np.array([self.i, self.q])

    def __add__(self, other):
        """Add two Waveform objects."""
        if not isinstance(other, Waveforms):
            raise NotImplementedError
        self.i = np.append(self.i, other.i)
        self.q = np.append(self.q, other.q)
        return self

    def __len__(self):
        """Length of the object."""
        if len(self.i) != len(self.q):
            raise ValueError("Both I and Q waveforms must have the same length.")
        return len(self.i)
