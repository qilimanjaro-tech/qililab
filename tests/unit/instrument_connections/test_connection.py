"""This file tests the the connection class"""
import pytest

from qililab.instrument_connections import Connection

class TestConnection:
    """This class contains the unit tests for the ``Connection`` class."""

    def test_error_raises_when_already_connected(self):
        test = Connection(settings = {"address": "test"})
        test._connected = True
        with pytest.raises(ValueError) as e:
            test.connect(device="test", device_name="test")
            assert str(e.value) == "Instrument (test_device) is already connected"