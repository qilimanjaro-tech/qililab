from dataclasses import dataclass

from qililab.qprogram.operations.operation import Operation


@dataclass(frozen=True)
class Sync(Operation):  # pylint: disable=missing-class-docstring
    buses: list[str] | None
