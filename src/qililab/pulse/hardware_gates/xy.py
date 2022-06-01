"""XY gate"""
from typing import Tuple

import numpy as np
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory


@HardwareGateFactory.register
class XY(HardwareGate):
    """XY gate."""

    class_type = gates.U2

    @classmethod
    def translate(cls, gate: gates.U2) -> Tuple[float, float]:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        theta, phi = gate.parameters
        theta = cls.normalize_angle(angle=theta)
        amplitude = np.abs(theta) / np.pi
        phase = (phi + 0 if theta >= 0 else np.pi) % (2 * np.pi)
        return amplitude, phase
