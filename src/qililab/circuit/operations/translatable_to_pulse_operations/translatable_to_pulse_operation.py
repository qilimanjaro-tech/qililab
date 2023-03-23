from dataclasses import dataclass, field

from qililab.circuit.operations.operation import Operation


@dataclass
class TranslatableToPulseOperation(Operation):
    """Operation that can be translated to pulse"""
