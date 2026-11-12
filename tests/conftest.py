# conftest.py
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, ContextManager

import pytest

from qililab.qililab_settings import get_settings


@pytest.fixture
def override_settings() -> Callable[..., ContextManager[None]]:
    """Temporarily override QililabSettings values inside tests."""

    @contextmanager
    def _override(**overrides: Any) -> Iterator[None]:
        settings = get_settings()
        original = {key: getattr(settings, key) for key in overrides}
        try:
            for key, value in overrides.items():
                setattr(settings, key, value)
            yield
        finally:
            for key, value in original.items():
                setattr(settings, key, value)

    return _override
