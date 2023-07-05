import numpy as np

from . import Gaussian  # TODO: Circular import problems. Should we use a factory, or something else...?
from .waveform import Waveform


class Drag(Waveform):
    # TODO: either allow the wave array to be loaded in this method if it has been calculated already
    # or have it cached (see the example in gaussian)
    def __init__(self, coefficient: float, waveform: Waveform, warray: np.ndarray | None = None):
        """Init method

        Args:
            coefficient (float): Drag coefficient
            waveform (Waveform): Waveform on which return the corrected drag
            warray (np.ndarray | None, optional): Uncorrected waveform array. Defaults to None.
        """
        self.waveform = waveform
        self.coeff = coefficient
        # get waveform array if it is not given
        self.warray = waveform.envelope() if warray is None else warray

    def envelope(self):
        """Envelope of the drag pulse, this will depend on the pulse shape
        we are applying corrections on
        """
        if isinstance(self.waveform, Gaussian):
            drag = (-1 * self.coeff * (self.waveform.time - self.waveform.mu_) / self.waveform.sigma**2) * self.warray

        return drag
