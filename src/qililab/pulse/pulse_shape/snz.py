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

"""SNZ pulse shape."""
from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from qililab.config import logger
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


@Factory.register
@dataclass(frozen=True, eq=True)
class SNZ(PulseShape):
    """Sudden net zero pulse shape. It is composed of a half-duration positive rectangular pulse, followed
    by three stops to cross height = 0, to then have another half-duration negative rectangular pulse.

    More concretely, the shape from left to right is composed by:
        - half-duration positive rectangular pulse.
        - instantaneous stop at height b.
        - t-phi duration at height = 0.
        - instantaneous stop at height -b.
        - half-duration negative rectangular pulse.

    Examples:
        To get the envelope of a SNZ shape, with ``b`` and ``t_phi`` equal to ``B`` and ``T``, you need to do:

        .. code-block:: python

            from qililab.pulse.pulse_shape import SNZ
            snz_envelope = SNZ(b=B, t_phi=T).envelope(amplitude=1, duration=50)

        which for ``b=0.2``, ``t_phi=2`` and ``b=0.5``, ``t_phi=10``, look respectively like:

        .. image:: /classes_images/snzs.png
            :width: 800
            :align: center

    References:
        High-fidelity controlled-Z gate with maximal intermediate leakage operating at the speed
        limit in a superconducting quantum processor: https://arxiv.org/abs/2008.07411

    Args:
        b (float): Instant stops height when going from the rectangular half-duration to `height = 0`.
        t_phi (int): Time at `height = 0`, in the middle of the positive and negative rectangular pulses.
    """

    name = PulseShapeName.SNZ  #: Name of the snz pulse shape.
    b: float  #: Instant stops height.
    t_phi: int  #: Time at `height = 0`.

    def __post_init__(self):
        # ensure t_phi is an int
        if not isinstance(self.t_phi, int):
            raise TypeError("t_phi for pulse SNZ has to be an integer. Since min time resolution is 1ns")

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0) -> np.ndarray:
        """Constant amplitude envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse
            resolution (float, optional): Resolution of the pulse. Defaults to 1.

        Returns:
            ndarray: Amplitude of the envelope for each time step.

        The duration of the each half-pulse is determined by the total pulse duration. Thus
        halfpulse_t = (duration - t_phi - 2) / 2. This implies that (duration - t_phi) should be even.
        The -2 in the formula above is due to the 2 impulses b.
        """
        # calculate the halfpulse duration
        halfpulse_t = (duration - 2 - self.t_phi) / 2
        halfpulse_t = int(halfpulse_t / resolution)

        envelope = np.zeros(round(duration / resolution))
        # raise warning if we are rounding
        if (duration / resolution) % 1 != 0 or (halfpulse_t / resolution) % 1 != 0:
            logger.warning(  # pylint: disable=logging-fstring-interpolation
                f"Envelope length rounded to nearest value {len(envelope)} from division full_snz_duration ({duration}) / resolution ({resolution}) = {duration/resolution}"
            )
        envelope[:halfpulse_t] = amplitude * np.ones(halfpulse_t)  # positive square halfpulse
        envelope[halfpulse_t] = self.b * amplitude  # impulse b
        envelope[halfpulse_t + 2 + self.t_phi :] = 0  # t_phi
        envelope[halfpulse_t + 1 + self.t_phi] = -self.b * amplitude  # impulse -b
        envelope[halfpulse_t + 2 + self.t_phi :] = -amplitude * np.ones(halfpulse_t)  # negative square halfpulse

        return envelope

    @classmethod
    def from_dict(cls, dictionary: dict) -> "SNZ":
        """Loads SNZ object/shape from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the SNZ object/shape, including the name of the pulse shape, the
            b parameter and the t_phi parameter.

        Returns:
            Rectangular: Loaded class.
        """
        local_dictionary = deepcopy(dictionary)
        local_dictionary.pop("name", None)
        return cls(**local_dictionary)

    def to_dict(self) -> dict:
        """Returns dictionary representation of the Rectangular object/shape.

        Returns:
            dict: Dictionary representation including the name of the pulse shape, the b parameter and the t_phi parameter..
        """
        return {
            "name": self.name.value,
            "b": self.b,
            "t_phi": self.t_phi,
        }
