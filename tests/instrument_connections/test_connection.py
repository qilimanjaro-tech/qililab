"""This file tests the the connection class"""

import re

import pytest

from qililab.instrument_connections.connection import Connection


class TestConnection:
    """This class contains the unit tests for the ``Connection`` class."""

    def test_error_raises_when_already_connected(self):
        """Test that ensure that an error rises when connecting an instrument that is already connected"""
        test = Connection(settings={"address": "test"})
        test._connected = True
        expected = re.escape("Instrument (test) is already connected")
        with pytest.raises(ValueError, match=expected):
            test.connect(device="test", device_name="test")
