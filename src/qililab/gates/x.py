from typing import Tuple

from qibo.gates import X as XQibo

from qililab.gates.hardware_gate import HardwareGate


class X(HardwareGate, XQibo):  # pylint: disable=invalid-name
    """X gate

    Args:
        q (int): Index of the qubit to which the gate is applied.
    """

    def amplitude_and_phase(self) -> Tuple[float, float]:
        """
        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        return 1, 0
