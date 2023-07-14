import numpy as np

from .waveform import Waveform


class Square(Waveform):
    """Square (rectangular) waveform"""

    def __init__(self, amplitude: float, duration: int):
        """Init method

        Args:
            amplitude (float): pulse amplitude
            duration (int): pulse duration
            resolution (int, optional): Pulse resolution. Defaults to 1.
        """
        self.amplitude = amplitude
        self.duration = duration

    def envelope(self, resolution: float = 1):
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
        return self.amplitude * np.ones(round(self.duration / resolution))
