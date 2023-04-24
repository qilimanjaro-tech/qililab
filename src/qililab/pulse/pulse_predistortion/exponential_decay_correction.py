"""Exponential decay correction."""
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.constants import RUNCARD
from qililab.typings import PulsePredistortionName
from qililab.typings.enums import PulseShapeSettingsName

from .predistorted_pulse import PredistortedPulse


@dataclass(unsafe_hash=True, frozen=True, eq=True)
class ExponentialCorrection(PredistortedPulse):
    """Exponential decay correction pulse shape."""

    name = PulsePredistortionName.EXPONENTIAL_CORRECTION
    tau_exponential: float
    amp: float
    sampling_rate: float = 1.0

    def envelope(self, duration: int | None = None, amplitude: float | None = None, resolution: float = 1.0):
        """Distorted square envelope.

        Corrects an exponential decay using a linear IIR filter.
        Fitting should be done to y = g*(1+amp*exp(-t/tau)), where g is ignored in the corrections.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """

        if amplitude is None:
            raise AttributeError("Sorry, can't predistort the Pulse without an amplitude.")

        if duration is None:
            raise AttributeError("Sorry, can't predistort the Pulse without a duration.")

        ysig = amplitude * np.ones(round(duration / resolution))

        if self.amp >= 0.0:
            # Parameters
            alpha = 1 - np.exp(-1 / (self.sampling_rate * self.tau_exponential * (1 + self.amp)))

            k = self.amp / (1 + self.amp - alpha)
            b = [(1 - k + k * alpha), -(1 - k) * (1 - alpha)]

            a = [1, -(1 - alpha)]

        # FIXME: Check if there should be another if here, or just a else.
        elif self.amp < 0.0:
            # Parameters
            a0 = 1
            a1 = (self.tau_exponential * (1 + 2 * self.amp) - 1) / (2 * self.tau_exponential * (1 + self.amp) + 1)

            b0 = (2 * self.tau_exponential + 1) / (2 * self.tau_exponential + (1 + self.amp) + 1)
            b1 = (-2 * self.tau_exponential + 1) / (2 * self.tau_exponential * (1 + self.amp + 1))

            a = [a0, a1]
            b = [b0, b1]

        else:
            raise TypeError("Sorry, can't predistort the Pulse if amp is not a defined float.")

        # Filtered signal
        ycorr = signal.lfilter(b, a, ysig)
        norm = np.amax(np.abs(ycorr))
        ycorr = (1 / norm) * ycorr

        amplitude = amplitude * ycorr / ysig

        return self.pulse.envelope(amplitude=amplitude, resolution=resolution)

    def to_dict(self):
        """Return dictionary representation of the pulse shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.TAU_EXPONENTIAL.value: self.tau_exponential,
            PulseShapeSettingsName.AMP.value: self.amp,
        }
