"""XY gate"""
import numpy as np
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.pulse.hardware_gates.x import X
from qililab.typings import GateName


@HardwareGateFactory.register
class XY(HardwareGate):
    """XY gate."""

    name = GateName.XY
    class_type = gates.U2

    @classmethod
    def translate(cls, gate: gates.U2) -> HardwareGate.HardwareGateSettings:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        # TODO: Scale X and Y rotations independently!
        x_settings = X.parameters()
        if x_settings is None:
            raise ValueError("Please specify the specifications of the X gate.")
        theta, phi = gate.parameters
        theta = cls.normalize_angle(angle=theta)
        amplitude = (np.abs(theta) / np.pi) * x_settings.amplitude
        phase = (phi if theta >= 0 else phi + np.pi) % (2 * np.pi)
        return cls.HardwareGateSettings(
            amplitude=amplitude, phase=phase, duration=x_settings.duration, shape=x_settings.shape
        )
