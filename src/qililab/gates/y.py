from typing import Tuple

import numpy as np
from qibo.gates import Y as YQibo

from qililab.gates.hardware_gate import HardwareGate


class Y(HardwareGate, YQibo):  # pylint: disable=invalid-name
    """Y gate

    Args:
        q (int): Index of the qubit to which the gate is applied.
    """

    def amplitude_and_phase(self) -> Tuple[float, float]:
        """
        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        return 0, np.pi / 2
