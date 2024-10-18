"""This file tests the the ``qblox_d5a`` class"""

from unittest.mock import MagicMock

import pytest

from qililab.instruments.qblox import QbloxD5a
from qililab.typings.enums import Parameter


@pytest.fixture(name="qblox_d5a")
def fixture_qblox_d5a():
    """Fixture that returns an instance of a dummy QbloxD5a."""
    return QbloxD5a(
        {
            "alias": "d5a",
            "voltage": [0],
            "span": [],
            "ramping_enabled": [],
            "ramp_rate": [],
            "dacs": []
        }
    )


class TestQbloxD5a:
    """This class contains the unit tests for the ``qblox_d5a`` class."""

    def test_error_raises_when_no_channel_specified(self, qblox_d5a):
        """These test makes soure that an error raises whenever a channel is not specified in chainging a parameter

        Args:
            qblox_d5a (_type_): _description_
        """
        name = qblox_d5a.name.value
        with pytest.raises(ValueError, match=f"channel not specified to update instrument {name}"):
            qblox_d5a.device = MagicMock()
            qblox_d5a.set_parameter(parameter=Parameter.VOLTAGE, value="2", channel_id=None)

    def test_setup_method_no_connection(self, qblox_d5a):
        """Test setup method."""
        qblox_d5a.set_parameter(parameter=Parameter.VOLTAGE, value=2, channel_id=0)
        assert qblox_d5a.settings.voltage[0] == 2.0

    def test_initial_setup_method_no_connection(self, qblox_d5a):
        """Test setup method."""
        with pytest.raises(RuntimeError, match=f"Device of instrument {qblox_d5a.alias} has not been initialized."):
            qblox_d5a.initial_setup()
            qblox_d5a
