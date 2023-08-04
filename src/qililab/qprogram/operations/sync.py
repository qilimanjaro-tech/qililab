from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass
class Sync(Operation):  # pylint: disable=missing-class-docstring
    buses: list[str] | None
