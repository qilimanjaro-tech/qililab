# conftest.py
import importlib.metadata as im
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any, ContextManager

import pytest

from qililab.qililab_settings import get_settings


def _has_qm():
    try:
        im.version("qm-qua")
        im.version("qualang-tools")
        return True
    except im.PackageNotFoundError:
        return False


def pytest_collection_modifyitems(config, items):
    run_qm = config.getoption("--run-qm", default=False)
    config.addinivalue_line("markers", "qm: requires QM optional dependency")

    for item in items:
        if "qm" in item.keywords:
            if not run_qm:
                item.add_marker(pytest.mark.skip(reason="qm tests are optional; use --run-qm"))
            elif not _has_qm():
                item.add_marker(pytest.mark.skip(reason="missing 'qm-qua'/'qualang-tools'"))


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
