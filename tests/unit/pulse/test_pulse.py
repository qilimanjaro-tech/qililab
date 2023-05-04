"""Tests for the Pulse class."""
import random

import numpy as np
import pytest

from qililab.constants import PULSE
from qililab.pulse import Drag, Gaussian, Pulse, PulseShape, Rectangular
from qililab.utils import Waveforms


class TestPulse:
    """Unit tests checking the Pulse attributes and methods"""

    def test_modulated_waveforms_method(self, pulse: Pulse):
        """Test modulated_waveforms method."""
        waveforms = pulse.modulated_waveforms()
        assert isinstance(waveforms, Waveforms)

    def test_envelope_method(self, pulse: Pulse):
        """Test envelope method"""
        envelope = pulse.envelope(amplitude=2.0, resolution=0.1)
        assert isinstance(envelope, np.ndarray)

    def test_to_dict_method(self, pulse: Pulse):
        """Test to_dict method"""
        dictionary = pulse.to_dict()
        assert isinstance(dictionary, dict)
