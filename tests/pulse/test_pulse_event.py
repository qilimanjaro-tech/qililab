"""Tests for the Pulse class."""

import itertools

import numpy as np
import pytest

from qililab.constants import PULSEEVENT
from qililab.pulse import (
    BiasTeeCorrection,
    Cosine,
    Drag,
    ExponentialCorrection,
    Gaussian,
    Pulse,
    PulseDistortion,
    PulseEvent,
    Rectangular,
)
from qililab.pulse.pulse_distortion.lfilter_correction import LFilterCorrection
from qililab.utils import Waveforms

# Parameters for the different Pulses
AMPLITUDE = [0.9]
PHASE = [0, np.pi / 3, 2 * np.pi]
DURATION = [48]
FREQUENCY = [0.7e9]
SHAPE = [
    Rectangular(),
    Cosine(),
    Cosine(lambda_2=0.3),
    Gaussian(num_sigmas=4),
    Drag(num_sigmas=4, drag_coefficient=1.0),
]

# Parameters for the different corrections.
TAU_BIAS_TEE = [1.3]
TAU_EXPONENTIAL = [0.9]
AMP = [-5.1, 0.8, 2.0]
NORM_FACTOR = 0.8


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
    """Fixture for the Pulse class."""
    return request.param


@pytest.fixture(
    name="pulse_distortions",
    params=[
        [
            ExponentialCorrection(tau_exponential=tau_exponential, amp=amp),
            BiasTeeCorrection(tau_bias_tee=tau_bias_tee, norm_factor=NORM_FACTOR),
            LFilterCorrection(a=[0.7, 1.3], b=[0.5, 0.6]),
        ]
        for tau_exponential, amp, tau_bias_tee in itertools.product(TAU_EXPONENTIAL, AMP, TAU_BIAS_TEE)
    ],
)
def fixture_pulse_distortions(request: pytest.FixtureRequest) -> ExponentialCorrection:
    """Fixture for the pulse distortion class."""
    return request.param


@pytest.fixture(name="pulse_event")
def fixture_pulse_event() -> PulseEvent:
    """Load PulseEvent.

    Returns:
        PulseEvent: Instance of the PulseEvent class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    return PulseEvent(pulse=pulse, start_time=0)


class TestPulseEvent:
    """Unit tests checking the PulseEvent attributes and methods"""

    def test_modulated_waveforms_method(self, pulse_event: PulseEvent):
        """Test modulated_waveforms method."""
        waveforms = pulse_event.modulated_waveforms()

        assert waveforms is not None
        assert isinstance(waveforms, Waveforms)
        assert len(waveforms.values[0]) == len(waveforms.values[1]) == len(pulse_event.envelope())

    def test_envelope_method(self, pulse: Pulse, pulse_distortions: list[PulseDistortion]):
        """Test envelope method"""
        pulse_event = PulseEvent(pulse=pulse, start_time=0, pulse_distortions=pulse_distortions)

        resolution = 0.1

        envelope = pulse_event.envelope()
        envelope2 = pulse_event.envelope(resolution=resolution)
        envelope3 = pulse_event.envelope(amplitude=2.0, resolution=resolution)

        for env in [envelope, envelope2, envelope3]:
            assert env is not None
            assert isinstance(env, np.ndarray)

            if pulse_distortions:
                assert not np.array_equal(pulse.envelope(), env)

        # Test maximums
        if isinstance(pulse.pulse_shape, Cosine) and pulse.pulse_shape.lambda_2 > 0.0:
            # If lambda_2 > 0.0 the max amplitude is reduced
            assert round(np.max(np.abs(np.real(envelope))), 2 * int(np.sqrt(1 / 1.0))) < NORM_FACTOR * pulse.amplitude
            assert (
                round(np.max(np.abs(np.real(envelope2))), int(np.sqrt(1 / resolution))) < NORM_FACTOR * pulse.amplitude
            )
            assert round(np.max(np.abs(np.real(envelope3))), int(np.sqrt(1 / resolution))) < NORM_FACTOR * 2.0
            # If you check the form of this shape, the maximum never gets down 70% of the Amplitude for any lambda_2
            assert (
                round(np.max(np.abs(np.real(envelope))), 2 * int(np.sqrt(1 / 1.0)))
                > NORM_FACTOR * 0.7 * pulse.amplitude
            )
            assert (
                round(np.max(np.abs(np.real(envelope2))), int(np.sqrt(1 / resolution)))
                > NORM_FACTOR * 0.7 * pulse.amplitude
            )
            assert round(np.max(np.abs(np.real(envelope3))), int(np.sqrt(1 / resolution))) > NORM_FACTOR * 0.7 * 2.0
        else:
            # In the rest of pulse_shapes the maximum is the amplitude
            assert round(np.max(np.abs(np.real(envelope))), 2 * int(np.sqrt(1 / 1.0))) == round(
                NORM_FACTOR * pulse.amplitude, 5
            )
            assert round(np.max(np.abs(np.real(envelope2))), int(np.sqrt(1 / resolution))) == round(
                NORM_FACTOR * pulse.amplitude, 5
            )
            assert round(np.max(np.abs(np.real(envelope3))), int(np.sqrt(1 / resolution))) == round(
                NORM_FACTOR * 2.0, 5
            )

        assert len(pulse.envelope()) == len(envelope)
        assert len(envelope) * 10 == len(envelope2) == len(envelope3)

    def test_from_dict_method(self, pulse: Pulse, pulse_distortions: list[PulseDistortion]):
        """Test to_dict method"""
        pulse_event = PulseEvent(pulse=pulse, start_time=0, pulse_distortions=pulse_distortions)

        dictionary = pulse_event.to_dict()
        pulse_event2 = PulseEvent.from_dict(dictionary)

        dictionary2 = pulse_event2.to_dict()
        pulse_event3 = PulseEvent.from_dict(dictionary2)

        for event in [pulse_event2, pulse_event3]:
            assert event is not None
            assert isinstance(event, PulseEvent)

        assert pulse_event == pulse_event2 == pulse_event3

    def test_to_dict_method(self, pulse: Pulse, pulse_distortions: list[PulseDistortion]):
        """Test to_dict method"""
        pulse_event = PulseEvent(pulse=pulse, start_time=0, pulse_distortions=pulse_distortions)
        dictionary = pulse_event.to_dict()

        pulse_event2 = PulseEvent.from_dict(dictionary)
        dictionary2 = pulse_event2.to_dict()

        for dict_ in [dictionary, dictionary2]:
            assert dict_ is not None
            assert isinstance(dict_, dict)

        assert (
            dictionary
            == dictionary2
            == {
                PULSEEVENT.PULSE: pulse_event.pulse.to_dict(),
                PULSEEVENT.START_TIME: pulse_event.start_time,
                PULSEEVENT.PULSE_DISTORTIONS: [distortion.to_dict() for distortion in pulse_event.pulse_distortions],
                "qubit": None,
            }
        )

    def test_end_time(self, pulse: Pulse, pulse_distortions: list[PulseDistortion]):
        """Test end_time property."""
        pulse_event = PulseEvent(pulse=pulse, start_time=0, pulse_distortions=pulse_distortions)
        duration = pulse_event.duration

        assert duration is not None
        assert isinstance(duration, int)
        assert duration == pulse_event.end_time - pulse_event.start_time
