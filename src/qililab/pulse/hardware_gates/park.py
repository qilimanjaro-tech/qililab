"""Parking gate"""
from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.transpiler import Park as Park_gate
from qililab.typings import GateName


@HardwareGateFactory.register
class Park(HardwareGate):  # pylint: disable=invalid-name
    """Park gate."""

    name = GateName.Park
    class_type = Park_gate

    @classmethod
    def translate(cls, gate: Park_gate) -> HardwareGate.HardwareGateSettings:
        """Translate gate into pulse.
        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """
        park_params = Park.settings[gate.target_qubits[0]]

        return cls.HardwareGateSettings(
            amplitude=park_params.amplitude,
            phase=park_params.phase,
            duration=park_params.duration,
            shape=park_params.shape,
        )