from functools import cached_property

import numpy as np

from .waveform import Waveform


class Gaussian(Waveform):
    """Gaussian waveform with peak at duration/2 and spanning for num_sigmas over the pule duration.

    The normal distribution's parameters mu (mean) and sigma (standard deviation) will be therefore
    defined by mu = duration / 2 and sigma = duration / num_sigmas
    """

    def __init__(self, amplitude: float, duration: int, num_sigmas: float, resolution: int = 1):
        """Init method

        Args:
            amplitude (float): pulse amplitude
            duration (int): pulse duration
            num_sigmas (float): number of sigmas in the gaussian pulse
            resolution (int, optional): Pulse resolution. Defaults to 1.
        """

        self.amplitude = amplitude
        self.duration = duration
        self.resolution = resolution
        self.num_sigmas = num_sigmas

        self.sigma = self.duration / self.num_sigmas
        self.mu = self.duration / 2

    # TODO: investigate https://docs.python.org/3/faq/programming.html#faq-cache-method-calls
    # this is so we don't call the envelope twice when applying a drag pulse?
    @cached_property
    def envelope(self):
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
        x = np.arange(self.duration / self.resolution) * self.resolution

        gaussian = self.amplitude * np.exp(-0.5 * (x - self.mu) ** 2 / self.sigma**2)
        norm = np.amax(np.real(gaussian))

        # TODO: do we want to do this like this?
        gaussian = gaussian - gaussian[0]  # Shift to avoid introducing noise at time 0
        corr_norm = np.amax(np.real(gaussian))

        return gaussian * norm / corr_norm
