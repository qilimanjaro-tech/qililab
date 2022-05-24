"""X gate"""
from typing import List, Tuple

from qibo import gates

from qililab.pulse.pulsed_gates.pulsed_gate import PulsedGate
from qililab.pulse.pulsed_gates.pulsed_gate_factory import PulsedGateFactory


@PulsedGateFactory.register
class X(PulsedGate):  # pylint: disable=invalid-name
    """X gate."""

    class_type = gates.X
    amplitude = 1
    phase = 0

    @classmethod
    def translate(cls, parameters: None | float | List[float]) -> Tuple[float, float]:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        return cls.amplitude, cls.phase
