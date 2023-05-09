"""Tests for the Pulse class."""
import itertools

import numpy as np
import pytest

from qililab.constants import PULSE
from qililab.pulse import Pulse
from qililab.pulse.pulse_shape import Drag, Gaussian, Rectangular
from qililab.utils import Waveforms

# Parameters for the different Pulses
AMPLITUDE = [0.9]
PHASE = [0, np.pi / 3, 2 * np.pi]
DURATION = [47]
FREQUENCY = [0.7e9]
RESOLUTION = [1.1]
SHAPE = [Rectangular(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, drag_coefficient=1.0)]


@pytest.fixture(
    name="pulse",
    params=[
        Pulse(amplitude=amplitude, phase=phase, duration=duration, frequency=frequency, pulse_shape=shape)
        for amplitude, phase, duration, frequency, shape in itertools.product(
            AMPLITUDE, PHASE, DURATION, FREQUENCY, SHAPE
        )
    ],
)
def fixture_pulses(request: pytest.FixtureRequest) -> Pulse:
    """Fixture for the pulse distortion class."""
    return request.param


class TestPulse:
    """Unit tests checking the Pulse attributes and methods"""

    def test_modulated_waveforms_method(self, pulse: Pulse):
        """Test modulated_waveforms method."""
        waveforms = pulse.modulated_waveforms()

        assert waveforms is not None
        assert isinstance(waveforms, Waveforms)

    def test_envelope_method(self, pulse: Pulse):
        """Test envelope method"""
        envelope = pulse.envelope()
        envelope2 = pulse.envelope(resolution=0.1)
        envelope3 = pulse.envelope(amplitude=2.0, resolution=0.1)

        assert envelope is not None and envelope2 is not None and envelope3 is not None
        assert isinstance(envelope, np.ndarray)
        assert isinstance(envelope2, np.ndarray)
        assert isinstance(envelope3, np.ndarray)
        assert round(np.max(np.abs(envelope)), 15) == pulse.amplitude
        assert round(np.max(np.abs(envelope2)), 15) == pulse.amplitude
        assert round(np.max(np.abs(envelope3)), 15) == 2.0
        assert len(envelope) * 10 == len(envelope2) == len(envelope3)

    def test_from_dict_method(self, pulse: Pulse):
        """Test to_dict method"""
        dictionary = pulse.to_dict()
        pulse2 = Pulse.from_dict(dictionary)
        dictionary2 = pulse2.to_dict()
        pulse3 = Pulse.from_dict(dictionary2)

        assert pulse2 is not None and pulse2 is not None
        assert isinstance(pulse2, Pulse) and isinstance(pulse3, Pulse)
        assert pulse == pulse2 and pulse2 == pulse3 and pulse3 == pulse

    def test_to_dict_method(self, pulse: Pulse):
        """Test to_dict method"""
        dictionary = pulse.to_dict()
        pulse2 = Pulse.from_dict(dictionary)
        dictionary2 = pulse2.to_dict()

        assert dictionary is not None and dictionary is not None
        assert isinstance(dictionary, dict) and isinstance(dictionary2, dict)
        assert dictionary == {
            PULSE.AMPLITUDE: pulse.amplitude,
            PULSE.FREQUENCY: pulse.frequency,
            PULSE.PHASE: pulse.phase,
            PULSE.DURATION: pulse.duration,
            PULSE.PULSE_SHAPE: pulse.pulse_shape.to_dict(),
        }
        assert dictionary2 == {
            PULSE.AMPLITUDE: pulse.amplitude,
            PULSE.FREQUENCY: pulse.frequency,
            PULSE.PHASE: pulse.phase,
            PULSE.DURATION: pulse.duration,
            PULSE.PULSE_SHAPE: pulse.pulse_shape.to_dict(),
        }
        assert dictionary == dictionary2
