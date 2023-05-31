"""Exponential decay correction (loop) pulse shape."""
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.typings.enums import PulseShapeSettingsName
from qililab.utils import Factory


@Factory.register
@dataclass(unsafe_hash=True, eq=True, frozen=True)
class ExponentialCorrectionLoop(PulseShape):
    """Exponential decay correction (loop) pulse shape."""

    name = PulseShapeName.EXPONENTIAL_CORRECTION_LOOP
    tau_exponential1: float
    tau_exponential2: float
    amp1: float
    amp2: float
    sampling_rate: float = 1.0

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Distorted square envelope.

        Corrects an exponential decay using a linear IIR filter.
        Fitting should be done to y = g*(1+amp*exp(-t/tau)), where g is ignored in the corrections.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """

        tau_exponential = [self.tau_exponential1, self.tau_exponential2]
        amp = [self.amp1, self.amp2]

        ysig = amplitude * np.ones(round(duration / resolution))

        for i in range(2):
            # Parameters
            alpha = 1 - np.exp(-1 / (self.sampling_rate * tau_exponential[i] * (1 + amp[i])))

            if amp[i] >= 0.0:
                k = amp[i] / (1 + amp[i] - alpha)
                b = [(1 - k + k * alpha), -(1 - k) * (1 - alpha)]
            else:
                k = -amp[i] / (1 + amp[i]) / (1 - alpha)
                b = [(1 + k - k * alpha), -(1 - k) * (1 - alpha)]

            a = [1, -(1 - alpha)]

            # Filtered signal
            ysig = signal.lfilter(b, a, ysig)
            norm = np.amax(np.abs(ysig))
            ysig = ysig / norm

        return ysig

    def to_dict(self):
        """Return dictionary representation of the pulse shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.TAU_EXPONENTIAL1.value: self.tau_exponential1,
            PulseShapeSettingsName.TAU_EXPONENTIAL2.value: self.tau_exponential2,
            PulseShapeSettingsName.AMP1.value: self.amp1,
            PulseShapeSettingsName.AMP2.value: self.amp2,
        }
