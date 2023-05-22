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
    """Sudden net zero pulse shape. See supplementary material I in https://arxiv.org/abs/2008.07411"""

    name = PulseShapeName.SNZ
    b: float
    t_phi: int

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Constant amplitude envelope.

        Args:
            duration (int): HALF-PULSE duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse
            resolution (float): Pulse resolution

        Returns:
            ndarray: Amplitude of the envelope for each time step.

        The duration of the pulse is determined by duration, which is the duration of a halfpulse
        thus the total duration will be 2*duration + t_phi + 2, where the 2 is due to each of the
        1ns b pulses
        """

        # ensure t_phi is an int or float with 0 decimal part
        if not isinstance(self.t_phi, int):
            if self.t_phi % 1 != 0:
                raise ValueError(
                    f"t_phi with value {self.t_phi}ns for pulse SNZ cannot have decimal part since min time resolution is 1ns"
                )
            else:
                self.t_phi = int(self.t_phi)
        full_snz_duration = 2 * duration + self.t_phi + 2
        envelope = np.zeros(round(full_snz_duration / resolution))
        # raise warning if we are rounding
        if (full_snz_duration / resolution) % 1 != 0 or (duration / resolution) % 1 != 0:
            logger.warning(
                f"Envelope length rounded to nearest value {len(envelope)} from division full_snz_duration ({full_snz_duration}) / resolution ({resolution}) = {full_snz_duration/resolution}"
            )
        halfpulse_t = int(duration / resolution)
        envelope[:halfpulse_t] = amplitude * np.ones(halfpulse_t)  # positive square halfpulse
        envelope[halfpulse_t] = self.b  # impulse b
        envelope[halfpulse_t + 2 + self.t_phi :] = 0  # t_phi
        envelope[halfpulse_t + 1 + self.t_phi] = -self.b  # impulse -b
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
