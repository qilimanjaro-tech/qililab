from dataclasses import dataclass

from qililab.circuit.operations.operation import Operation


@dataclass
class SpecialOperation(Operation):
    """Operation that has a special implementation"""

    pass
