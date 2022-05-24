"""RX gate"""
from typing import List, Tuple

import numpy as np
from qibo import gates

from qililab.pulse.pulsed_gates.pulsed_gate import PulsedGate
from qililab.pulse.pulsed_gates.pulsed_gate_factory import PulsedGateFactory


@PulsedGateFactory.register
class RX(PulsedGate):
    """RX gate."""

    class_type = gates.RX

    @classmethod
    def translate(cls, parameters: None | float | List[float]) -> Tuple[float, float]:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        if not isinstance(parameters, float):
            raise ValueError("RX gate received a wrong parameter value.")

        theta = parameters
        theta = (theta) % (2 * np.pi)
        if theta > np.pi:
            theta -= 2 * np.pi
        amplitude = np.abs(theta) / np.pi
        phase = 0 if theta >= 0 else np.pi
        return amplitude, phase
