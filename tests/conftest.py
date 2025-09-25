# conftest.py
import importlib.metadata as im

import pytest


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
