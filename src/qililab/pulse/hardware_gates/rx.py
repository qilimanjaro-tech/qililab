"""RX gate"""
import numpy as np
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.pulse.hardware_gates.x import X
from qililab.typings import GateName


@HardwareGateFactory.register
class RX(HardwareGate):
    """RX gate."""

    name = GateName.RX
    class_type = gates.RX

    @classmethod
    def translate(
        cls,
        gate: gates.RX,
        master_amplitude_gate: float,
        master_duration_gate: int,
    ) -> HardwareGate.HardwareGateSettings:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        x_params = X.parameters(
            master_amplitude_gate=master_amplitude_gate,
            master_duration_gate=master_duration_gate,
        )
        (theta,) = gate.parameters
        theta = cls.normalize_angle(angle=theta)  # normalize is setting theta to [-pi,pi]
        amplitude = (np.abs(theta) / np.pi) * x_params.amplitude
        phase = x_params.phase if theta >= 0 else x_params.phase + np.pi
        return cls.HardwareGateSettings(
            amplitude=amplitude, phase=phase, duration=x_params.duration, shape=x_params.shape
        )
