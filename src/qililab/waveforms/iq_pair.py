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

"""IQPair dataclass."""

from __future__ import annotations

from qililab.qprogram.decorators import requires_domain
from qililab.qprogram.variable import Domain
from qililab.waveforms.drag_correction import DragCorrection
from qililab.waveforms.gaussian import Gaussian
from qililab.waveforms.iq_waveform import IQWaveform
from qililab.waveforms.waveform import Waveform
from qililab.yaml import yaml


@yaml.register_class
class IQPair(IQWaveform):
    """IQPair dataclass, containing the 'in-phase' (I) and 'quadrature' (Q) parts of a signal."""
    def __init__(self, I: Waveform, Q: Waveform):
        if not isinstance(I, Waveform) or not isinstance(Q, Waveform):
            raise TypeError("Waveform inside IQPair must have Waveform type.")

        if I.get_duration() != Q.get_duration():
            raise ValueError("Waveforms of an IQ pair must have the same duration.")
        self.I = I
        self.Q = Q

    def get_I(self) -> Waveform:
        return self.I

    def get_Q(self) -> Waveform:
        return self.Q

    def get_duration(self) -> int:
        """Get the duration of the waveforms

        Returns:
            int: The duration of the waveforms.
        """
        return self.I.get_duration()

    @requires_domain("amplitude", Domain.Voltage)
    @requires_domain("duration", Domain.Time)
    @requires_domain("num_sigmas", Domain.Scalar)
    @requires_domain("drag_coefficient", Domain.Scalar)
    @staticmethod
    def DRAG(amplitude: float, duration: int, num_sigmas: float, drag_coefficient: float) -> IQPair:
        """Create a DRAG pulse. This is an IQ pair where the I channel corresponds to the gaussian wave and the Q is the drag correction, which corresponds to the derivative of the I channel times a ``drag_coefficient``.

        Args:
            amplitude (float): Maximum amplitude of the pulse.
            duration (int): Duration of the pulse (ns).
            num_sigmas (float): Sigma number of the gaussian pulse shape. Defines the width of the gaussian pulse.
            drag_coefficient (float): Drag coefficient that gives the DRAG its imaginary components.
        """
        waveform_i = Gaussian(amplitude=amplitude, duration=duration, num_sigmas=num_sigmas)
        waveform_q = DragCorrection(drag_coefficient=drag_coefficient, waveform=waveform_i)

        return IQPair(I=waveform_i, Q=waveform_q)
