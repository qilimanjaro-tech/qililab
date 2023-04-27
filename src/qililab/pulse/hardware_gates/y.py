"""Y gate"""
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.typings import GateName


@HardwareGateFactory.register
class Y(HardwareGate):  # pylint: disable=invalid-name
    """Y gate."""

    name = GateName.Y
    class_type = gates.Y

    @classmethod
    def translate(
        cls,
        gate: gates.Y,
        master_amplitude_gate: float,
        master_duration_gate: int,
    ) -> HardwareGate.HardwareGateSettings:
        """Translate gate into pulse.

        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """
        return cls.parameters(
            master_amplitude_gate=master_amplitude_gate,
            master_duration_gate=master_duration_gate,
        )
