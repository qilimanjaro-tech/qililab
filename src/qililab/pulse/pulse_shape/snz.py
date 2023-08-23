"""SNZ pulse shape."""
from dataclasses import dataclass

import numpy as np

from qililab.config import logger
from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.typings.enums import PulseShapeSettingsName
from qililab.utils import Factory


@Factory.register
@dataclass(frozen=True, eq=True)
class SNZ(PulseShape):
    """Sudden net zero pulse shape. It is composed of a half-duration positive rectangular pulse, followed
    by three stops to cross height = 0, to then have another half-duration negative rectangular pulse.\

    |   --------------                      <- half-duration positive rectangular pulse
    |                 -                     <- instantaneous stop at height b
    0                  ---                  <- t-phi duration at height = 0
    |                     -                 <- instantaneous stop at height -b
    |                      -------------    <- half-duration negative rectangular pulse

    References:
        High-fidelity controlled-Z gate with maximal intermediate leakage operating at the speed
        limit in a superconducting quantum processor: https://arxiv.org/abs/2008.07411

    Args:
        b (float): instant stops height when going from the rectangular half-duration to height=0.
        t_phi (int): time at height=0, in the middle of the positive and negative rectangular pulses.
    """

    name = PulseShapeName.SNZ
    b: float
    t_phi: int

    def __post_init__(self):
        # ensure t_phi is an int
        if not isinstance(self.t_phi, int):
            raise TypeError("t_phi for pulse SNZ has to be an integer. Since min time resolution is 1ns")

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Constant amplitude envelope.

        Args:
            duration (int): total pulse duration (ns).
            amplitude (float): Maximum amplitude of the pulse
            resolution (float): Pulse resolution

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
        """Load SNZ object/shape from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the SNZ object/shape.

        Returns:
            Rectangular: Loaded class.
        """
        local_dictionary = dictionary.copy()
        local_dictionary.pop(RUNCARD.NAME, None)
        return cls(**local_dictionary)

    def to_dict(self):
        """Return dictionary representation of the Rectangular object/shape.

        Returns:
            dict: Dictionary.
        """

        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.B.value: self.b,
            PulseShapeSettingsName.T_PHI.value: self.t_phi,
        }
