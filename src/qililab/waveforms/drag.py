import numpy as np

from .waveform import Waveform


class DragCorrection(Waveform):
    def __init__(self, coefficient: float, waveform: Waveform):
        """Init method

        Args:
            coefficient (float): Drag coefficient
            waveform (Waveform): Waveform on which return the corrected drag
        """
        self.waveform = waveform
        self.coeff = coefficient

    def envelope(self):
        from . import (  # TODO: Circular import problems. Should we use a factory, or something else...? So far importing in envelope should work as a fix
            Gaussian,
        )

        """Envelope of the drag pulse, this will depend on the pulse shape
        we are applying corrections on
        """
        if isinstance(self.waveform, Gaussian):
            drag = (
                -1 * self.coeff * (self.waveform.time - self.waveform.mu_) / self.waveform.sigma**2
            ) * self.waveform.envelope  # envelope of the original is calculated every time

        return drag
