from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass
class Sync(Operation):
    buses: list[str]
