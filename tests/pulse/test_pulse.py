"""Tests for the Pulse class."""
import itertools

import numpy as np
import pytest

from qililab.constants import PULSE
from qililab.pulse import Cosine, Drag, Gaussian, Pulse, Rectangular

# Parameters for the different Pulses
AMPLITUDE = [0, 0.9, 1.1, -0.8]
PHASE = [0, np.pi / 3, 2 * np.pi]
DURATION = [47, 40]
FREQUENCY = [0.7e9]
SHAPE = [
    Rectangular(),
    Cosine(),
    Cosine(lambda_2=0.3),
    Gaussian(num_sigmas=4),
    Drag(num_sigmas=4, drag_coefficient=1.0),
]

# Parameters of the envelope.
RESOLUTION = 1.0


@pytest.mark.parametrize(
    "pulse",
    [
        Pulse(amplitude=amplitude, phase=phase, duration=duration, frequency=frequency, pulse_shape=shape)
        for amplitude, phase, duration, frequency, shape in itertools.product(
            AMPLITUDE, PHASE, DURATION, FREQUENCY, SHAPE
        )
    ],
)
class TestPulse:
    """Unit tests checking the Pulse attributes and methods"""

    def test_envelope_method(self, pulse: Pulse):
        """Test envelope method"""
        envelope = pulse.envelope(resolution=RESOLUTION)

        # Test not None and type
        assert envelope is not None
        assert isinstance(envelope, np.ndarray)

        # Assert size of np.ndarray
        assert len(envelope) == pulse.duration / RESOLUTION

        # Test the maximums of the positive envelopes
        if pulse.amplitude >= 0.0:
            if isinstance(pulse.pulse_shape, Cosine) and pulse.pulse_shape.lambda_2 > 0.0:
                # If lambda_2 > 0.0 the max amplitude is reduced, but never gets down 70% of the Amplitude
                assert round(np.max(np.real(envelope)), 2) <= pulse.amplitude
                assert round(np.max(np.real(envelope)), 2) >= 0.7 * pulse.amplitude
            else:
                assert round(np.max(np.real(envelope)), 2) == pulse.amplitude

        # Test the minimums of the negative envelopes
        elif pulse.amplitude <= 0.0:
            if isinstance(pulse.pulse_shape, Cosine) and pulse.pulse_shape.lambda_2 > 0.0:
                # If lambda_2 > 0.0 the max amplitude is reduced, but never gets down 70% of the Amplitude
                assert round(np.min(np.real(envelope)), 2) >= pulse.amplitude
                assert round(np.min(np.real(envelope)), 2) <= 0.7 * pulse.amplitude
            else:
                assert round(np.min(np.real(envelope)), 2) == pulse.amplitude

        # Test the 0 amplitude case
        elif pulse.amplitude == 0.0:
            assert 0.0 == np.max(envelope) == np.min(envelope)

    def test_from_dict_method(self, pulse: Pulse):
        """Test to_dict method"""
        dictionary = pulse.to_dict()
        pulse2 = Pulse.from_dict(dictionary)

        dictionary2 = pulse2.to_dict()
        pulse3 = Pulse.from_dict(dictionary2)

        for p in [pulse2, pulse3]:
            assert p is not None
            assert isinstance(p, Pulse)

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
