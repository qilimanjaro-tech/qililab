from dataclasses import dataclass, field

from qililab.circuit.operations.operation import Operation
from qililab.typings import OperationName
from qililab.typings.enums import OperationMultiplicity


@dataclass
class TranslatableToPulseOperation(Operation):
    """Operation that can be translated to pulse"""

    pass
