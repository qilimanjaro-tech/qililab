"""Dit factory."""
from typing import Any, List, Tuple


def dict_factory(data: List[Tuple[str, Any]]):
    """Dict factory used in the asdict() dataclass function. Avoid None values."""
    return {key: value for (key, value) in data if value is not None}
