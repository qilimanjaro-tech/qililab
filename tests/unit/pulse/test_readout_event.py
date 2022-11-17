"""Tests for the Pulse class."""
import numpy as np
import pytest

from qililab.pulse import ReadoutEvent
from qililab.utils import Waveforms


class TestReadoutEvent:
    """Unit tests checking the attributes and methods"""

    def test_to_dict_method(self, pulse_event: ReadoutEvent):
        """Test to_dict method"""
        dictionary = pulse_event.to_dict()
        assert isinstance(dictionary, dict)
