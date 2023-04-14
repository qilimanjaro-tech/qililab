"""This file tests the the connection class"""
import pytest
import re

from qililab.instrument_connections import Connection

class TestConnection:
    """This class contains the unit tests for the ``Connection`` class."""

    def test_error_raises_when_already_connected(self):
        test = Connection(settings = {"address": "test"})
        test._connected = True
        expected = re.escape("Instrument (test) is already connected")
        with pytest.raises(ValueError, match=expected):
            test.connect(device="test", device_name="test")