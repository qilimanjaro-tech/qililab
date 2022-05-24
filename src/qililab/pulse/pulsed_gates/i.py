"""Identity gate"""
from typing import List, Tuple

from qibo import gates

from qililab.pulse.pulsed_gates.pulsed_gate import PulsedGate
from qililab.pulse.pulsed_gates.pulsed_gate_factory import PulsedGateFactory


@PulsedGateFactory.register
class I(PulsedGate):  # pylint: disable=invalid-name # noqa: E742
    """Identity gate."""

    class_type = gates.I
    amplitude = 0
    phase = 0

    @classmethod
    def translate(cls, parameters: None | float | List[float]) -> Tuple[float, float]:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        return cls.amplitude, cls.phase
