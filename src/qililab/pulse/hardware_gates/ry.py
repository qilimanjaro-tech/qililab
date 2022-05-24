"""RX gate"""
from typing import Tuple

import numpy as np
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory


@HardwareGateFactory.register
class RY(HardwareGate):
    """RY gate."""

    class_type = gates.RY

    @classmethod
    def translate(cls, gate: gates.RY) -> Tuple[float, float]:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        theta = gate.parameters
        theta = (theta) % (2 * np.pi)
        if theta > np.pi:
            theta -= 2 * np.pi
        amplitude = np.abs(theta) / np.pi
        phase = np.pi / 2 if theta >= 0 else 3 * np.pi / 4
        return amplitude, phase
