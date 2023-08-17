"""Tests for the ExponentialCorrection distortion class."""
import itertools

import numpy as np
import pytest

from qililab.constants import RUNCARD
from qililab.pulse import Pulse
from qililab.pulse.pulse_distortion import ExponentialCorrection
from qililab.pulse.pulse_shape import SNZ, Cosine, Drag, Gaussian, Rectangular
from qililab.typings.enums import PulseDistortionSettingsName

# Parameters for the ExponentialCorrection.
TAU_EXPONENTIAL = [0.7, 1.3]
AMP = [-5.1, 0.8, 2.1]

# Parameters of the Pulse and its envelope.
AMPLITUDE = [0.9]
PHASE = [0, np.pi / 3]
DURATION = [48]
FREQUENCY = [0.7e9]
RESOLUTION = [1.0]
SHAPE = [Rectangular(), Cosine(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, drag_coefficient=1.0), SNZ(b=0.1, t_phi=4)]


@pytest.fixture(
    name="pulse_distortion",
    params=[
        ExponentialCorrection(tau_exponential=tau_exponential, amp=amp)
        for tau_exponential, amp in itertools.product(TAU_EXPONENTIAL, AMP)
    ],
)
def fixture_pulse_distortion(request: pytest.FixtureRequest) -> ExponentialCorrection:
    """Fixture for the ExponentialCorrection distortion class."""
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


class TestExponentialCorrection:
    """Unit tests checking the ExponentialCorrection attributes and methods"""

    def test_apply(self, pulse_distortion: ExponentialCorrection, envelope: np.ndarray):
        """Test for the envelope method."""
        norm_factors = [1.0, 0.75]
        corr_envelopes = [pulse_distortion.apply(envelope=envelope)]
        corr_envelopes.append(
            ExponentialCorrection(tau_exponential=1.3, amp=2.0, norm_factor=norm_factors[0]).apply(
                envelope=corr_envelopes[0]
            )
        )
        corr_envelopes.append(
            ExponentialCorrection(tau_exponential=0.5, amp=-5.0, norm_factor=norm_factors[1]).apply(
                envelope=corr_envelopes[1]
            )
        )
        not_corr_envelopes = [
            ExponentialCorrection(tau_exponential=0.9, amp=-5.0, auto_norm=False).apply(envelope=corr_envelopes[2])
        ]

        for corr_envelope in corr_envelopes:
            assert corr_envelope is not None
            assert isinstance(corr_envelope, np.ndarray)
            assert len(envelope) == len(corr_envelope)
            assert not np.array_equal(corr_envelope, envelope)
            assert np.max((np.real(corr_envelope))) <= 1
            assert np.min((np.real(corr_envelope))) >= -1

        for not_corr_envelope in not_corr_envelopes:
            assert not_corr_envelope is not None
            assert isinstance(not_corr_envelope, np.ndarray)
            assert len(envelope) == len(not_corr_envelope)
            assert not np.array_equal(not_corr_envelope, envelope)

        assert (
            round(np.max(np.abs(np.real(corr_envelopes[0]))), 14)
            == round(np.max(np.abs(np.real(corr_envelopes[1]))) / norm_factors[0], 14)
            == round(np.max(np.abs(np.real(corr_envelopes[2]))) / (norm_factors[0] * norm_factors[1]), 14)
            == round(np.max(np.abs(np.real(envelope))) * pulse_distortion.norm_factor, 14)
            != round(np.max(np.abs(np.real(not_corr_envelopes[0]))) / (norm_factors[0] * norm_factors[1]), 14)
        )

    def test_from_dict(self, pulse_distortion: ExponentialCorrection):
        """Test for the to_dict method."""
        dictionary = pulse_distortion.to_dict()
        pulse_distortions = [ExponentialCorrection.from_dict(dictionary)]

        dictionary.pop(PulseDistortionSettingsName.SAMPLING_RATE.value)
        pulse_distortions.append(ExponentialCorrection.from_dict(dictionary))

        dictionary.pop(RUNCARD.NAME)
        pulse_distortions.append(ExponentialCorrection.from_dict(dictionary))

        dictionary[PulseDistortionSettingsName.TAU_EXPONENTIAL.value] = 0.5
        dictionary[PulseDistortionSettingsName.AMP.value] = 1.2
        dictionary[PulseDistortionSettingsName.SAMPLING_RATE.value] = 2.0
        pulse_distortions.append(ExponentialCorrection.from_dict(dictionary))

        for distortion in pulse_distortions:
            assert distortion is not None
            assert isinstance(distortion, ExponentialCorrection)

    def test_to_dict(self, pulse_distortion: ExponentialCorrection):
        """Test for the to_dict method."""
        dictionary = pulse_distortion.to_dict()

        assert dictionary is not None
        assert isinstance(dictionary, dict)
        assert dictionary == {
            RUNCARD.NAME: pulse_distortion.name.value,
            PulseDistortionSettingsName.TAU_EXPONENTIAL.value: pulse_distortion.tau_exponential,
            PulseDistortionSettingsName.AMP.value: pulse_distortion.amp,
            PulseDistortionSettingsName.SAMPLING_RATE.value: pulse_distortion.sampling_rate,
            PulseDistortionSettingsName.NORM_FACTOR.value: pulse_distortion.norm_factor,
            PulseDistortionSettingsName.AUTO_NORM.value: pulse_distortion.auto_norm,
        }

    def test_serialization(self, pulse_distortion: ExponentialCorrection):
        """Test that a serialization of the distortion is possible"""
        dictionary = pulse_distortion.to_dict()
        assert isinstance(dictionary, dict)

        new_pulse_distortion = ExponentialCorrection.from_dict(dictionary)
        assert isinstance(new_pulse_distortion, ExponentialCorrection)

        new_dictionary = new_pulse_distortion.to_dict()
        assert isinstance(new_dictionary, dict)
        assert new_dictionary == dictionary
