from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass
class ResetPhase(Operation):  # pylint: disable=missing-class-docstring
    bus: str
