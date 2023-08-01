from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Element:
    _uuid: UUID = field(default_factory=uuid4, init=False)
