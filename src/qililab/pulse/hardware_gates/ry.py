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
    def translate(cls, gate: gates.RY) -> HardwareGate.HardwareGateSettings:
        """Translate gate into pulse.

        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """
        qubit = gate.target_qubits[0]
        y_params = Y.settings[qubit]
        (theta,) = gate.parameters
        theta = cls.normalize_angle(angle=theta)
        amplitude = (np.abs(theta) / np.pi) * y_params.amplitude
        phase = y_params.phase if theta >= 0 else y_params.phase + np.pi
        return cls.HardwareGateSettings(
            amplitude=amplitude, phase=phase, duration=y_params.duration, shape=y_params.shape
        )