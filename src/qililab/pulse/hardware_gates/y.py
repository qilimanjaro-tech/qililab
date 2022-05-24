"""Y gate"""
from typing import Tuple

import numpy as np
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory


@HardwareGateFactory.register
class Y(HardwareGate):  # pylint: disable=invalid-name
    """Y gate."""

    class_type = gates.Y
    amplitude = 1
    phase = np.pi / 2

    @classmethod
    def translate(cls, gate: gates.Y) -> Tuple[float, float]:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        return cls.amplitude, cls.phase
