import numpy as np

from .waveform import Waveform


class Gaussian(Waveform):
    """Gaussian waveform with peak at duration/2 and spanning for num_sigmas over the pule duration.

    The normal distribution's parameters mu (mean) and sigma (standard deviation) will be therefore
    defined by mu = duration / 2 and sigma = duration / num_sigmas
    """

    def __init__(self, amplitude: float, duration: int, num_sigmas: float):
        """Init method

        Args:
            amplitude (float): pulse amplitude
            duration (int): pulse duration
            num_sigmas (float): number of sigmas in the gaussian pulse
        """

        self.amplitude = amplitude
        self.duration = duration
        self.num_sigmas = num_sigmas

        # This allows to later modify these values to have different gaussian shapes
        # eg. displace the peak of the gaussian from the center of duration
        self.sigma = self.duration / self.num_sigmas
        self.mu = self.duration / 2

    def envelope(self, resolution: float = 1):
        """Returns the pulse matrix

        Args:
            resolution (int, optional): Pulse resolution. Defaults to 1.

        Returns:
            np.ndarray: pulse matrix
            resolution (int, optional): Pulse resolution. Defaults to 1.
        """
        x = np.arange(self.duration / resolution) * resolution

        gaussian = self.amplitude * np.exp(-0.5 * (x - self.mu) ** 2 / self.sigma**2)
        norm = np.amax(np.real(gaussian))

        gaussian = gaussian - gaussian[0]  # Shift to avoid introducing noise at time 0
        corr_norm = np.amax(np.real(gaussian))

        gaussian = gaussian * norm / corr_norm if norm != 0 else gaussian  # handle amplitude 0 corner case

        return gaussian
