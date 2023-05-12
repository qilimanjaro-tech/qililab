"""Tests for the pulse distortion class."""
import itertools

import numpy as np
import pytest

from qililab.constants import RUNCARD
from qililab.pulse import Pulse
from qililab.pulse.pulse_distortion import BiasTeeCorrection, ExponentialCorrection
from qililab.pulse.pulse_distortion.pulse_distortion import PulseDistortion
from qililab.pulse.pulse_shape import Drag, Gaussian, Rectangular
from qililab.typings.enums import PulseDistortionSettingsName
from qililab.utils import Factory

# Parameters for the different corrections.
TAU_BIAS_TEE = [0.7, 1.3]
TAU_EXPONENTIAL = [0.7, 1.3]
AMP = [-5.1, 0.8, 2.1]

# Parameters of the Pulse and its envelope.
AMPLITUDE = [0.9]
PHASE = [0, np.pi / 3, 2 * np.pi]
DURATION = [47]
FREQUENCY = [0.7e9]
RESOLUTION = [1.1]
SHAPE = [Rectangular(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, drag_coefficient=1.0)]


@pytest.fixture(
    name="pulse_distortion",
    params=[
        ExponentialCorrection(tau_exponential=tau_exponential, amp=amp)
        for tau_exponential, amp in itertools.product(TAU_EXPONENTIAL, AMP)
    ]
    + [BiasTeeCorrection(tau_bias_tee=tau_bias_tee) for tau_bias_tee in TAU_BIAS_TEE],
)
def fixture_pulse_distortion(request: pytest.FixtureRequest) -> ExponentialCorrection:
    """Fixture for the pulse distortion class."""
    return request.param


@pytest.fixture(
    name="envelope",
    params=[
        Pulse(amplitude=amplitude, phase=phase, duration=duration, frequency=frequency, pulse_shape=shape).envelope(
            resolution=resolution
        )
        for amplitude, phase, duration, frequency, resolution, shape in itertools.product(
            AMPLITUDE, PHASE, DURATION, FREQUENCY, RESOLUTION, SHAPE
        )
    ],
)
def fixture_envelope(request: pytest.FixtureRequest) -> np.ndarray:
    """Fixture for the pulse distortion class."""
    return request.param


class TestPulseDistortion:
    """Unit tests checking the PulseDistortion attributes and methods"""

    def test_apply(self, pulse_distortion: PulseDistortion, envelope: np.ndarray):
        """Test for the apply method."""
        corr_envelopes = [pulse_distortion.apply(envelope=envelope)]
        corr_envelopes.append(ExponentialCorrection(tau_exponential=1.3, amp=2.0).apply(envelope=corr_envelopes[0]))
        corr_envelopes.append(BiasTeeCorrection(tau_bias_tee=0.5).apply(envelope=corr_envelopes[1]))
        corr_envelopes.append(ExponentialCorrection(tau_exponential=0.5, amp=-5.0).apply(envelope=corr_envelopes[1]))

        for corr_envelope in corr_envelopes:
            assert corr_envelope is not None
            assert isinstance(corr_envelope, np.ndarray)
            assert len(envelope) == len(corr_envelope)
            assert round(np.max(np.real(corr_envelope)), 14) == round(np.max(np.real(envelope)), 14)
            assert not np.array_equal(corr_envelope, envelope)

    def test_from_dict(self, pulse_distortion: PulseDistortion):
        """Test for the to_dict method."""
        dictionary = pulse_distortion.to_dict()
        pulse_distortion2: PulseDistortion = Factory.get(name=pulse_distortion.name).from_dict(dictionary)

        dictionary2 = pulse_distortion2.to_dict()
        pulse_distortion3: PulseDistortion = Factory.get(name=pulse_distortion2.name).from_dict(dictionary2)

        assert isinstance(pulse_distortion2, Factory.get(name=pulse_distortion.name))
        assert isinstance(pulse_distortion3, Factory.get(name=pulse_distortion2.name))
        assert pulse_distortion2 is not None and pulse_distortion3 is not None
        assert isinstance(pulse_distortion2, PulseDistortion) and isinstance(pulse_distortion3, PulseDistortion)
        assert pulse_distortion == pulse_distortion2 == pulse_distortion3

    def test_to_dict(self, pulse_distortion: PulseDistortion):
        """Test for the to_dict method."""
        dictionary = pulse_distortion.to_dict()

        assert dictionary is not None
        assert isinstance(dictionary, dict)

        if isinstance(pulse_distortion, BiasTeeCorrection):
            assert dictionary == {
                RUNCARD.NAME: pulse_distortion.name.value,
                PulseDistortionSettingsName.TAU_BIAS_TEE.value: pulse_distortion.tau_bias_tee,
                PulseDistortionSettingsName.SAMPLING_RATE.value: pulse_distortion.sampling_rate,
            }

        if isinstance(pulse_distortion, ExponentialCorrection):
            assert dictionary == {
                RUNCARD.NAME: pulse_distortion.name.value,
                PulseDistortionSettingsName.TAU_EXPONENTIAL.value: pulse_distortion.tau_exponential,
                PulseDistortionSettingsName.AMP.value: pulse_distortion.amp,
                PulseDistortionSettingsName.SAMPLING_RATE.value: pulse_distortion.sampling_rate,
            }
