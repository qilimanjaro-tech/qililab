"""This file tests the the ``qblox_d5a`` class"""
import pytest

from qililab.typings.enums import Parameter
from qililab.instruments.qblox import QbloxD5a
from unittest.mock import MagicMock

@pytest.fixture(name="pulsar")
def fixture_pulsar_controller_qcm():
    """Fixture that returns an instance of a dummy QbloxD5a."""
    return QbloxD5a({'voltage':[],
                     'span':[],
                     'ramping_enabled':[],
                     'ramp_rate':[],
                     'dacs':[],
                     'firmware':"0.7.0",
                     'id_':1,
                     'category': "awg"
                     })  # pylint: disable=abstract-class-instantiated

class TestQblox_d5a:
    """This class contains the unit tests for the ``qblox_d5a`` class."""

    def test_error_raises_when_no_channel_specified(self, pulsar):
        with pytest.raises(ValueError, match="channel not specified to update instrument D5a"):
            pulsar.device = MagicMock()
            pulsar.setup(parameter = Parameter.VOLTAGE, value = '2', channel_id = None)