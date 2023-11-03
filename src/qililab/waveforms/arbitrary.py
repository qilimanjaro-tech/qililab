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

"""Arbitrary waveform."""
import numpy as np

from .waveform import Waveform


class Arbitrary(Waveform):  # pylint: disable=too-few-public-methods, disable=missing-class-docstring
    """Arbitrary waveform. Creates a waveform with the passed envelope.

    Args:
        envelope(np.ndarray): Passed envelope to base the waveform on.

    Examples:
        If you want to create a waveform with an envelope given by:

        .. code-block:: python

            import numpy as np
            original_envelope = np.ones(50)

        You would just need to do:

        .. code-block:: python

            import qililab as ql
            arbitrary_envelope = ql.Arbitrary(envelope=original_envelope)
    """

    def __init__(self, envelope: np.ndarray):
        self.samples = envelope

    def envelope(self) -> np.ndarray:
        """Returns the originally passed envelope.

        Returns:
            np.ndarray: Height of the envelope for each time step.
        """
        return self.samples
