from typing import Tuple

from qibo.gates import I as IQibo

from qililab.gates.hardware_gate import HardwareGate


class I(HardwareGate, IQibo):  # noqa: E742 # pylint: disable=invalid-name
    """Identity gate

    Args:
        q (int): Index of the qubit to which the gate is applied.
    """

    def amplitude_and_phase(self) -> Tuple[float, float]:
        """
        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        return 0, 0
