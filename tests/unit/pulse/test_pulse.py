"""Tests for the Pulse class."""
import itertools

import numpy as np
import pytest

from qililab.constants import PULSE
from qililab.pulse import Pulse, Drag, Gaussian, Rectangular
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


@pytest.fixture(name="pulse")
def fixture_pulse() -> Pulse:
    """Load Pulse.

    Returns:
        Pulse: Instance of the Pulse class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    return Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)


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

        for env in [envelope, envelope2, envelope3]:
            assert env is not None
            assert isinstance(env, np.ndarray)

        assert round(np.max(np.real(envelope)), 14) == pulse.amplitude
        assert round(np.max(np.real(envelope2)), 14) == pulse.amplitude
        assert round(np.max(np.real(envelope3)), 14) == 2.0

        assert len(envelope) * 10 == len(envelope2) == len(envelope3)

        if isinstance(pulse.pulse_shape, Rectangular):
            assert np.max(envelope) == np.min(envelope)

        if isinstance(pulse.pulse_shape, Gaussian):
            assert np.max(envelope) == envelope[len(envelope) // 2]
            assert np.max(envelope) / 2 < envelope[len(envelope) // 4]
            assert np.min(envelope) == envelope[0]

        if isinstance(pulse.pulse_shape, Drag):
            assert np.max(np.real(envelope)) == np.real(envelope[len(envelope) // 2])
            assert np.max(np.real(envelope)) / 2 < np.real(envelope[len(envelope) // 4])
            assert np.min(np.real(envelope)) == np.real(envelope[0])

    def test_from_dict_method(self, pulse: Pulse):
        """Test to_dict method"""
        dictionary = pulse.to_dict()
        pulse2 = Pulse.from_dict(dictionary)

        dictionary2 = pulse2.to_dict()
        pulse3 = Pulse.from_dict(dictionary2)

        for pulse in [pulse2, pulse3]:
            assert pulse is not None
            assert isinstance(pulse, Pulse)

        assert pulse == pulse2 == pulse3

    def test_to_dict_method(self, pulse: Pulse):
        """Test to_dict method"""
        dictionary = pulse.to_dict()

        pulse2 = Pulse.from_dict(dictionary)
        dictionary2 = pulse2.to_dict()

        for dict_ in [dictionary, dictionary2]:
            assert dict_ is not None
            assert isinstance(dict_, dict)

        assert (
            dictionary
            == dictionary2
            == {
                PULSE.AMPLITUDE: pulse.amplitude,
                PULSE.FREQUENCY: pulse.frequency,
                PULSE.PHASE: pulse.phase,
                PULSE.DURATION: pulse.duration,
                PULSE.PULSE_SHAPE: pulse.pulse_shape.to_dict(),
            }
        )
