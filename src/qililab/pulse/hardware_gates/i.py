"""Identity gate"""
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.typings import GateName


@HardwareGateFactory.register
class I(HardwareGate):  # pylint: disable=invalid-name # noqa: E742
    """Identity gate."""

    name = GateName.I
    class_type = gates.I

    @classmethod
    def translate(
        cls,
        gate: gates.I,  # noqa: E741
        master_amplitude_gate: float,
        master_duration_gate: int,
    ) -> HardwareGate.HardwareGateSettings:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        return cls.parameters(master_amplitude_gate=master_amplitude_gate, master_duration_gate=master_duration_gate)
