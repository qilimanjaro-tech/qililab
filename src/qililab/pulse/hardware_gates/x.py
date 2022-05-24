"""X gate"""
from typing import Tuple

from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory


@HardwareGateFactory.register
class X(HardwareGate):  # pylint: disable=invalid-name
    """X gate."""

    class_type = gates.X
    amplitude = 1
    phase = 0

    @classmethod
    def translate(cls, gate: gates.X) -> Tuple[float, float]:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        return cls.amplitude, cls.phase
