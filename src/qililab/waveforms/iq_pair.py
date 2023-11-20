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

"""IQPair dataclass."""
from dataclasses import dataclass

from qililab.waveforms.waveform import Waveform


@dataclass
class IQPair:  # pylint: disable=missing-class-docstring
    """IQPair dataclass, containing the 'in-phase' (I) and 'quadrature' (Q) parts of a signal."""

    I: Waveform
    Q: Waveform

    def __post_init__(self):
        if self.I.get_duration() != self.Q.get_duration():
            raise ValueError("Waveforms of an IQ pair must have the same duration.")

    def get_duration(self) -> int:
        """Get the duration of the waveforms

        Returns:
            int: The duration of the waveforms.
        """
        return self.I.get_duration()
