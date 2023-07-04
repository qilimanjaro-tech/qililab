import numpy as np


class Square:
    def __init__(self, amplitude: float, duration: int, resolution: int):
        self.amplitude = amplitude
        self.duration = duration
        self.resolution = resolution

    def envelope(self):
        return self.amplitude * np.ones(round(self.duration / self.resolution))
