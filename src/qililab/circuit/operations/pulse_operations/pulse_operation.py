from dataclasses import dataclass, field

from qililab.circuit.operations.operation import Operation


@dataclass
class PulseOperation(Operation):
    """Operation representing a generic pulse

    Args:
        amplitude (float): amplitude of the pulse
        duration (int): duration of the pulse in ns
    """

    amplitude: float
    duration: int
