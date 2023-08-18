"""Tests for the Pulse class."""
import itertools

import numpy as np
import pytest

from qililab.constants import PULSE
from qililab.pulse import Cosine, Drag, Gaussian, Pulse, Rectangular

# Parameters for the different Pulses
AMPLITUDE = [0.9]
PHASE = [0, np.pi / 3, 2 * np.pi]
DURATION = [47]
FREQUENCY = [0.7e9]
RESOLUTION = [1.1]
SHAPE = [
    Rectangular(),
    Cosine(),
    Cosine(lambda_2=0.3),
    Gaussian(num_sigmas=4),
    Drag(num_sigmas=4, drag_coefficient=1.0),
]


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
        resolution = 0.1

        envelope = pulse.envelope()
        envelope2 = pulse.envelope(resolution=resolution)
        envelope3 = pulse.envelope(amplitude=2.0, resolution=resolution)

        for env in [envelope, envelope2, envelope3]:
            assert env is not None
            assert isinstance(env, np.ndarray)

        if isinstance(pulse.pulse_shape, Cosine) and pulse.pulse_shape.lambda_2 > 0.0:
            # If lambda_2 > 0.0 the max amplitude is reduced
            assert round(np.max(np.real(envelope)), 2 * int(np.sqrt(1 / 1.0))) < pulse.amplitude
            assert round(np.max(np.real(envelope2)), int(np.sqrt(1 / resolution))) < pulse.amplitude
            assert round(np.max(np.real(envelope3)), int(np.sqrt(1 / resolution))) < 2.0
            # If you check the form of this shape, the maximum never gets down 70% of the Amplitude for any lambda_2
            assert round(np.max(np.real(envelope)), 2 * int(np.sqrt(1 / 1.0))) > 0.7 * pulse.amplitude
            assert round(np.max(np.real(envelope2)), int(np.sqrt(1 / resolution))) > 0.7 * pulse.amplitude
            assert round(np.max(np.real(envelope3)), int(np.sqrt(1 / resolution))) > 0.7 * 2.0

        else:
            assert round(np.max(np.real(envelope)), 2 * int(np.sqrt(1 / 1.0))) == pulse.amplitude
            assert round(np.max(np.real(envelope2)), int(np.sqrt(1 / resolution))) == pulse.amplitude
            assert round(np.max(np.real(envelope3)), int(np.sqrt(1 / resolution))) == 2.0

        assert len(envelope) * 10 == len(envelope2) == len(envelope3)

        if isinstance(pulse.pulse_shape, Rectangular):
            assert np.max(envelope) == np.min(envelope)

        if isinstance(pulse.pulse_shape, Cosine) and pulse.pulse_shape.lambda_2 > 0.0:
            assert np.max(envelope) != envelope[len(envelope) // 2]
            assert np.min(envelope) == envelope[0]

        if isinstance(pulse.pulse_shape, Cosine) and pulse.pulse_shape.lambda_2 <= 0.0:
            assert np.max(envelope) == envelope[len(envelope) // 2]
            assert np.min(envelope) == envelope[0]

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
