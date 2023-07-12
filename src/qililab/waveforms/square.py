import numpy as np

from .waveform import Waveform


class Square(Waveform):
    """Square (rectangular) waveform"""

    def __init__(self, amplitude: float, duration: int, resolution: int = 1):
        """Init method

        Args:
            amplitude (float): pulse amplitude
            duration (int): pulse duration
            resolution (int, optional): Pulse resolution. Defaults to 1.
        """
        self.amplitude = amplitude
        self.duration = duration
        self.resolution = resolution

    def envelope(self):
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
        return self.amplitude * np.ones(round(self.duration / self.resolution))
