import numpy as np


class Arbitrary:
    def __init__(self, samples: np.ndarray, resolution: int):
        self.samples = samples
        self.duration = len(samples) * resolution
        self.resolution = resolution

    def envelope(self):
        return self.samples
