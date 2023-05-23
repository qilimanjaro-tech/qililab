"""This file tests the the ``qblox_d5a`` class"""
from unittest.mock import MagicMock

import pytest

from qililab.instruments.qblox import QbloxS4g
from qililab.typings.enums import Parameter


@pytest.fixture(name="pulsar")
def fixture_pulsar_controller_qcm():
    """Fixture that returns an instance of a dummy QbloxD5a."""
    return QbloxS4g(
        {
            "current": [],
            "span": [],
            "ramping_enabled": [],
            "ramp_rate": [],
            "firmware": "0.7.0",
            "dacs": [],
            "id_": 1,
            "category": "awg",
        }
    )  # pylint: disable=abstract-class-instantiated


class TestQbloxS4g:
    """This class contains the unit tests for the ``qblox_d5a`` class."""

    def test_error_raises_when_no_channel_specified(self, pulsar):
        """These test makes soure that an error raises whenever a channel is not specified in chainging a parameter

        Args:
            pulsar (_type_): _description_
        """
        name = pulsar.name.value
        with pytest.raises(ValueError, match=f"channel not specified to update instrument {name}"):
            pulsar.device = MagicMock
            pulsar.setup(parameter=Parameter, value="2", channel_id=None)
