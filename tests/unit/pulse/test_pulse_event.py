"""Tests for the Pulse class."""
import itertools

import numpy as np
import pytest

from qililab.constants import PULSEEVENT
from qililab.pulse import Pulse, PulseEvent
from qililab.pulse.pulse_distortion import BiasTeeCorrection, ExponentialCorrection, PulseDistortion
from qililab.pulse.pulse_shape import Drag, Gaussian, Rectangular
from qililab.utils import Waveforms

# Parameters for the different Pulses
AMPLITUDE = [0.9]
PHASE = [0, np.pi / 3, 2 * np.pi]
DURATION = [47]
FREQUENCY = [0.7e9]
SHAPE = [Rectangular(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, drag_coefficient=1.0)]

# Parameters for the different corrections.
TAU_BIAS_TEE = [1.3]
TAU_EXPONENTIAL = [0.9]
AMP = [-5.1, 0.8, 2.0]


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


@pytest.fixture(
    name="pulse_distortions",
    params=[
        []
        + [
            ExponentialCorrection(tau_exponential=tau_exponential, amp=amp),
            BiasTeeCorrection(tau_bias_tee=tau_bias_tee),
            ExponentialCorrection(tau_exponential=tau_exponential, amp=amp),
        ]
        for tau_exponential, amp, tau_bias_tee in itertools.product(TAU_EXPONENTIAL, AMP, TAU_BIAS_TEE)
    ],
)
def fixture_pulse_distortions(request: pytest.FixtureRequest) -> ExponentialCorrection:
    """Fixture for the pulse distortion class."""
    return request.param


class TestPulseEvent:
    """Unit tests checking the PulseEvent attributes and methods"""

    def test_modulated_waveforms_method(self, pulse_event: PulseEvent):
        """Test modulated_waveforms method."""
        waveforms = pulse_event.modulated_waveforms()

        assert waveforms is not None
        assert isinstance(waveforms, Waveforms)

    def test_envelope_method(self, pulse: Pulse, pulse_distortions: list[PulseDistortion]):
        """Test envelope method"""
        pulse_event = PulseEvent(pulse=pulse, start_time=0, pulse_distortions=pulse_distortions)
        envelope = pulse_event.envelope()
        envelope2 = pulse_event.envelope(resolution=0.1)
        envelope3 = pulse_event.envelope(amplitude=2.0, resolution=0.1)

        for env in [envelope, envelope2, envelope3]:
            assert env is not None
            assert isinstance(env, np.ndarray)

            if pulse_distortions:
                assert not np.array_equal(pulse.envelope(), env)

        assert round(np.max(np.abs(envelope)), 15) == pulse.amplitude
        assert round(np.max(np.abs(envelope2)), 15) == pulse.amplitude
        assert round(np.max(np.abs(envelope3)), 15) == 2.0
        assert len(pulse.envelope()) == len(envelope)
        assert len(envelope) * 10 == len(envelope2) == len(envelope3)

    def test_from_dict_method(self, pulse: Pulse, pulse_distortions: list[PulseDistortion]):
        """Test to_dict method"""
        pulse_event = PulseEvent(pulse=pulse, start_time=0, pulse_distortions=pulse_distortions)
        dictionary = pulse_event.to_dict()
        pulse_event2 = PulseEvent.from_dict(dictionary)
        dictionary2 = pulse_event2.to_dict()
        pulse_event3 = PulseEvent.from_dict(dictionary2)

        assert pulse_event2 is not None and pulse_event3 is not None
        assert isinstance(pulse_event2, PulseEvent) and isinstance(pulse_event3, PulseEvent)
        assert pulse_event == pulse_event2 == pulse_event3

    def test_to_dict_method(self, pulse: Pulse, pulse_distortions: list[PulseDistortion]):
        """Test to_dict method"""
        pulse_event = PulseEvent(pulse=pulse, start_time=0, pulse_distortions=pulse_distortions)
        dictionary = pulse_event.to_dict()
        pulse_event2 = PulseEvent.from_dict(dictionary)
        dictionary2 = pulse_event2.to_dict()

        assert dictionary is not None and dictionary2 is not None
        assert isinstance(dictionary, dict) and isinstance(dictionary2, dict)
        assert (
            dictionary
            == dictionary2
            == {
                PULSEEVENT.PULSE: pulse_event.pulse.to_dict(),
                PULSEEVENT.START_TIME: pulse_event.start_time,
                PULSEEVENT.PULSE_DISTORTIONS: [distortion.to_dict() for distortion in pulse_event.pulse_distortions],
            }
        )

    def test_end_time(self, pulse_event: PulseEvent):
        """Test end_time property."""
        assert pulse_event.duration is not None
        assert isinstance(pulse_event.duration, int)
        assert pulse_event.duration == pulse_event.end_time - pulse_event.start_time
