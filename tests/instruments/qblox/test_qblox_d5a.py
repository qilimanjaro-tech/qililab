"""This file tests the the ``qblox_d5a`` class"""
from unittest.mock import MagicMock

import pytest

from qililab.instruments.qblox import QbloxD5a
from qililab.typings.enums import Parameter


@pytest.fixture(name="pulsar")
def fixture_pulsar_controller_qcm():
    """Fixture that returns an instance of a dummy QbloxD5a."""
    return QbloxD5a(
        {
            "alias": "d5a",
            "voltage": [0],
            "span": [],
            "ramping_enabled": [],
            "ramp_rate": [],
            "dacs": [],
            "firmware": "0.7.0",
        }
    )  # pylint: disable=abstract-class-instantiated


class TestQbloxD5a:
    """This class contains the unit tests for the ``qblox_d5a`` class."""

    def test_error_raises_when_no_channel_specified(self, pulsar):
        """These test makes soure that an error raises whenever a channel is not specified in chainging a parameter

        Args:
            pulsar (_type_): _description_
        """
        name = pulsar.name.value
        with pytest.raises(ValueError, match=f"channel not specified to update instrument {name}"):
            pulsar.device = MagicMock()
            pulsar.setup(parameter=Parameter.VOLTAGE, value="2", channel_id=None)

    def test_setup_method_no_connection(self, pulsar):
        """Test setup method."""
        pulsar.setup(parameter=Parameter.VOLTAGE, value=2, channel_id=0)
        assert pulsar.settings.voltage[0] == 2.0

    def test_initial_setup_method_no_connection(self, pulsar):
        """Test setup method."""
        with pytest.raises(AttributeError, match="Instrument Device has not been initialized"):
            pulsar.initial_setup()
