"""Tests for the BiasTeeCorrection distortion class."""
import itertools

import numpy as np
import pytest

from qililab.constants import RUNCARD
from qililab.pulse import Pulse
from qililab.pulse.pulse_distortion import BiasTeeCorrection
from qililab.pulse.pulse_shape import SNZ, Cosine, Drag, Gaussian, Rectangular
from qililab.typings.enums import PulseDistortionSettingsName

# Parameters for the BiasTeeCorrection.
TAU_BIAS_TEE = [0.7, 1.3]

# Parameters of the Pulse and its envelope.
AMPLITUDE = [0.9]
PHASE = [0, 2 * np.pi]
DURATION = [48]
FREQUENCY = [0.7e9]
RESOLUTION = [1.1]
SHAPE = [Rectangular(), Cosine(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, drag_coefficient=1.0), SNZ(b=0.2, t_phi=2)]


@pytest.fixture(
    name="pulse_distortion",
    params=[BiasTeeCorrection(tau_bias_tee=tau_bias_tee) for tau_bias_tee in TAU_BIAS_TEE],
)
def fixture_pulse_distortion(request: pytest.FixtureRequest) -> BiasTeeCorrection:
    """Fixture for the BiasTeeCorrection distortion class."""
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


class TestBiasTeeCorrection:
    """Unit tests checking the BiasTeeCorrection attributes and methods"""

    def test_apply(self, pulse_distortion: BiasTeeCorrection, envelope: np.ndarray):
        """Test for the envelope method."""
        norm_factors = [0.85, 0.15]
        corr_envelopes = [pulse_distortion.apply(envelope=envelope)]
        corr_envelopes.append(
            BiasTeeCorrection(tau_bias_tee=1.3, norm_factor=norm_factors[0]).apply(envelope=corr_envelopes[0])
        )
        corr_envelopes.append(
            BiasTeeCorrection(tau_bias_tee=0.5, norm_factor=norm_factors[1]).apply(envelope=corr_envelopes[1])
        )
        corr_envelopes.append(BiasTeeCorrection(tau_bias_tee=0.9).apply(envelope=corr_envelopes[2]))
        not_corr_envelopes = [BiasTeeCorrection(tau_bias_tee=0.9, auto_norm=False).apply(envelope=corr_envelopes[2])]
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

    def test_from_dict(self, pulse_distortion: BiasTeeCorrection):
        """Test for the to_dict method."""
        dictionary = pulse_distortion.to_dict()
        pulse_distortions = [BiasTeeCorrection.from_dict(dictionary)]

        dictionary.pop(PulseDistortionSettingsName.SAMPLING_RATE.value)
        pulse_distortions.append(BiasTeeCorrection.from_dict(dictionary))

        dictionary.pop(RUNCARD.NAME)
        pulse_distortions.append(BiasTeeCorrection.from_dict(dictionary))

        dictionary[PulseDistortionSettingsName.TAU_BIAS_TEE.value] = 0.5
        dictionary[PulseDistortionSettingsName.SAMPLING_RATE.value] = 2.0
        pulse_distortions.append(BiasTeeCorrection.from_dict(dictionary))

        for distortion in pulse_distortions:
            assert distortion is not None
            assert isinstance(distortion, BiasTeeCorrection)

    def test_to_dict(self, pulse_distortion: BiasTeeCorrection):
        """Test for the to_dict method."""
        dictionary = pulse_distortion.to_dict()

        assert dictionary is not None
        assert isinstance(dictionary, dict)
        assert dictionary == {
            RUNCARD.NAME: pulse_distortion.name.value,
            PulseDistortionSettingsName.TAU_BIAS_TEE.value: pulse_distortion.tau_bias_tee,
            PulseDistortionSettingsName.SAMPLING_RATE.value: pulse_distortion.sampling_rate,
            PulseDistortionSettingsName.NORM_FACTOR.value: pulse_distortion.norm_factor,
            PulseDistortionSettingsName.AUTO_NORM.value: pulse_distortion.auto_norm,
        }

    def test_serialization(self, pulse_distortion: BiasTeeCorrection):
        """Test that a serialization of the distortion is possible"""
        dictionary = pulse_distortion.to_dict()
        assert isinstance(dictionary, dict)

        new_pulse_distortion = BiasTeeCorrection.from_dict(dictionary)
        assert isinstance(new_pulse_distortion, BiasTeeCorrection)

        new_dictionary = new_pulse_distortion.to_dict()
        assert isinstance(new_dictionary, dict)
        assert new_dictionary == dictionary
