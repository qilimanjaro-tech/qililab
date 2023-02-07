"""RX gate"""
import numpy as np
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.pulse.hardware_gates.y import Y
from qililab.typings import GateName


@HardwareGateFactory.register
class RY(HardwareGate):
    """RY gate."""

    name = GateName.RY
    class_type = gates.RY

    @classmethod
    def translate(
        cls,
        gate: gates.RY,
        master_amplitude_gate: float,
        master_duration_gate: int,
    ) -> HardwareGate.HardwareGateSettings:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        y_params = Y.parameters(
            master_amplitude_gate=master_amplitude_gate,
            master_duration_gate=master_duration_gate,
        )
        (theta,) = gate.parameters
        theta = cls.normalize_angle(angle=theta)
        amplitude = (np.abs(theta) / np.pi) * y_params.amplitude
        phase = y_params.phase if theta >= 0 else y_params.phase + np.pi
        return cls.HardwareGateSettings(
            amplitude=amplitude, phase=phase, duration=y_params.duration, shape=y_params.shape
        )
