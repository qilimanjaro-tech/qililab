"""This file tests the the ``qblox_d5a`` class"""

from unittest.mock import MagicMock

import pytest

from qililab.instruments.qblox import QbloxS4g
from qililab.typings.enums import Parameter


@pytest.fixture(name="s4g")
def fixture_s4g():
    """Fixture that returns an instance of a dummy QbloxD5a."""
    return QbloxS4g(
        {
            "alias": "s4g",
            "current": [],
            "span": [],
            "ramping_enabled": [],
            "ramp_rate": [],
            "dacs": [],
        }
    )


class TestQbloxS4g:
    """This class contains the unit tests for the ``qblox_d5a`` class."""
