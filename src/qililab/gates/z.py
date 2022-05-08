from typing import Tuple

from qibo.gates import Z as ZQibo

from qililab.gates.hardware_gate import HardwareGate


class Z(HardwareGate, ZQibo):  # pylint: disable=invalid-name
    """Z gate

    Args:
        q (int): Index of the qubit to which the gate is applied.
    """

    def amplitude_and_phase(self) -> Tuple[float, float]:
        """
        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        raise NotImplementedError
