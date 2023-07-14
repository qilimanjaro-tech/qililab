from qililab.waveforms.drag_correction import DragCorrection
from qililab.waveforms.gaussian import Gaussian

from .iq_pair import IQPair


class Drag(IQPair):
    """Drag pulse. This is a gaussian drive pulse with an IQ pair where the I channel corresponds to the gaussian wave
    and the Q is the drag correction, which corresponds to the derivative of the I channel times a drag_coefficient
    """

    def __init__(self, drag_coefficient: float, amplitude: float, duration: int, num_sigmas: float):
        """Init method

        Args:
            drag_coefficient (float): drag coefficient
            amplitude (float): amplitude of the pulse
            duration (int): duration of the pulse
            num_sigmas (float): number of sigmas in the gaussian pulse
        """
        waveform_i = Gaussian(amplitude=amplitude, duration=duration, num_sigmas=num_sigmas)
        waveform_q = DragCorrection(drag_coefficient=drag_coefficient, waveform=waveform_i)

        super().__init__(I=waveform_i, Q=waveform_q)
