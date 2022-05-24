"""Y gate"""
from typing import List, Tuple

import numpy as np
from qibo import gates

from qililab.pulse.pulsed_gates.pulsed_gate import PulsedGate
from qililab.pulse.pulsed_gates.pulsed_gate_factory import PulsedGateFactory


@PulsedGateFactory.register
class Y(PulsedGate):  # pylint: disable=invalid-name
    """Y gate."""

    class_type = gates.Y
    amplitude = 1
    phase = np.pi / 2

    @classmethod
    def translate(cls, parameters: None | float | List[float]) -> Tuple[float, float]:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        return cls.amplitude, cls.phase
