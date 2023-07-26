"""Identity gate"""
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.settings.gate_settings import CircuitPulseSettings
from qililab.typings import GateName


@HardwareGateFactory.register
class I(HardwareGate):  # pylint: disable=invalid-name # noqa: E742
    """Identity gate."""

    name = GateName.I
    class_type = gates.I

    @classmethod
    def translate(
        cls, gate: gates.I, gate_schedule: list[CircuitPulseSettings]  # noqa: E741
    ) -> list[CircuitPulseSettings]:
        """Translate gate into pulse.

        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """
        return gate_schedule
