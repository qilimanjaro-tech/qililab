"""Identity gate"""
from typing import Tuple

from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory


@HardwareGateFactory.register
class I(HardwareGate):  # pylint: disable=invalid-name # noqa: E742
    """Identity gate."""

    class_type = gates.I
    amplitude = 0
    phase = 0

    @classmethod
    def translate(cls, gate: gates.I) -> Tuple[float, float]:  # noqa: E741
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        return cls.amplitude, cls.phase
