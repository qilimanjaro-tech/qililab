# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Drag IQPair."""
from qililab.waveforms.drag_correction import DragCorrection
from qililab.waveforms.gaussian import Gaussian

from .iq_pair import IQPair


class Drag(IQPair):  # pylint: disable=too-few-public-methods
    """Drag pulse. This is a gaussian drive pulse with an IQ pair where the I channel corresponds to the gaussian wave
    and the Q is the drag correction, which corresponds to the derivative of the I channel times a ``drag_coefficient``.

    Args:
        amplitude (float): Maximum amplitude of the pulse.
        duration (int): Duration of the pulse (ns).
        num_sigmas (float): Sigma number of the gaussian pulse shape. Defines the width of the gaussian pulse.
        drag_coefficient (float): Drag coefficient that gives the DRAG its imaginary components.
    """

    def __init__(self, amplitude: float, duration: int, num_sigmas: float, drag_coefficient: float):
        waveform_i = Gaussian(amplitude=amplitude, duration=duration, num_sigmas=num_sigmas)
        waveform_q = DragCorrection(drag_coefficient=drag_coefficient, waveform=waveform_i)

        super().__init__(I=waveform_i, Q=waveform_q)
