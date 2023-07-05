import numpy as np

from .waveform import Waveform


class Sine(Waveform):
    """General sine wave.

    Use the parameters dephasing or halfpulses to start the sine wave at a different phase
    than 0 (default) and halfpulses to do n halfpulses (default is 1) in the total duration.

    For example a full sine wave would be dephasing=0, halfpulses=2 to have both the positive
    and negative halfpulse.
    A cosine wave would be dephasing=np.pi/2, halfpulses=2.
    """

    def __init__(
        self, amplitude: float, duration: int, dephasing: float = 0, halfpulses: float = 1, resolution: int = 1
    ):
        """Init method

        Args:
            amplitude (float): pulse amplitude
            duration (int): pulse duration
            dephasing (float, optional): Sine wave phase offset. Defaults to 0.
            halfpulses (float, optional): Sine wave halfpulses. Defaults to 1.
            resolution (int, optional): Pulse resolution. Defaults to 1.
        """
        self.amplitude = amplitude
        self.duration = duration
        self.dephasing = dephasing
        self.halfpulses = halfpulses
        self.resolution = resolution

    def envelope(self) -> np.ndarray:
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """

        x = np.linspace(self.dephasing, self.halfpulses * np.pi, np.round(self.duration / self.resolution))
        return self.amplitude * np.sin(x)
