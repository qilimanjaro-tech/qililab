import numpy as np

from .waveform import Waveform


class Square(Waveform):  # pylint: disable=too-few-public-methods
    """Square (rectangular) waveform"""

    def __init__(self, amplitude: float, duration: int):
        """Init method

        Args:
            amplitude (float): pulse amplitude
            duration (int): pulse duration
        """
        self.amplitude = amplitude
        self.duration = duration

    def envelope(self, resolution: float = 1):
        """Returns the pulse matrix

        Args:
            resolution (int, optional): Pulse resolution. Defaults to 1.

        Returns:
            np.ndarray: pulse matrix
        """
        return self.amplitude * np.ones(round(self.duration / resolution))
