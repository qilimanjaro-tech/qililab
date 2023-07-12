import numpy as np

from .waveform import Waveform


class Drag(Waveform):
    """Gaussian waveform with peak at duration/2 and spanning for num_sigmas over the pule duration.

    The normal distribution's parameters mu (mean) and sigma (standard deviation) will be therefore
    defined by mu = duration / 2 and sigma = duration / num_sigmas
    """

    def __init__(
        self, drag_coefficient: float, amplitude: float, duration: int, num_sigmas: float, resolution: int = 1
    ):
        """Init method

        Args:
            drag_coefficient (float): drag coefficient
            amplitude (float): pulse amplitude
            duration (int): pulse duration
            num_sigmas (float): number of sigmas in the gaussian pulse
            resolution (int, optional): Pulse resolution. Defaults to 1.
        """
        self.drag_coefficient = drag_coefficient
        self.amplitude = amplitude
        self.duration = duration
        self.resolution = resolution
        self.num_sigmas = num_sigmas

        self.sigma = self.duration / self.num_sigmas
        self.mu = self.duration / 2

    def envelope(self):
        """Returns the pulse pair

        Returns:
            tuple[np.ndarray, np.ndarray]: pulse arrays in the I and Q channels
        """

        x = np.arange(self.duration / self.resolution) * self.resolution

        gaussian = self.amplitude * np.exp(-0.5 * (x - self.mu) ** 2 / self.sigma**2)
        norm = np.amax(np.real(gaussian))

        gaussian = gaussian - gaussian[0]  # Shift to avoid introducing noise at time 0
        corr_norm = np.amax(np.real(gaussian))

        drag_i = gaussian * norm / corr_norm
        drag_q = (-1 * self.drag_coefficient * (x - self.mu) / self.sigma**2) * drag_i
        return drag_i, drag_q
