"""Tests for the LFilterCorrection distortion class."""
import itertools

import numpy as np
import pytest

from qililab.constants import RUNCARD
from qililab.pulse import Pulse
from qililab.pulse.pulse_distortion import LFilterCorrection
from qililab.pulse.pulse_shape import SNZ, Cosine, Drag, Gaussian, Rectangular
from qililab.typings.enums import PulseDistortionSettingsName

# Parameters for the LFilterCorrection.
NORM_FACTOR = [0.95]
A = [[0.7, 1.3], [0.8, 0.6]]
B = [[0.5, 0.6], [0.8, 1.3]]

# Parameters of the Pulse and its envelope.
AMPLITUDE = [0.9]
PHASE = [np.pi / 3, 2 * np.pi]
DURATION = [48]
FREQUENCY = [0.7e9]
RESOLUTION = [1.0]
SHAPE = [Rectangular(), Cosine(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, drag_coefficient=1.0), SNZ(b=0.1, t_phi=2)]


@pytest.fixture(
    name="pulse_distortion",
    params=[
        LFilterCorrection(a=a, b=b, norm_factor=norm_factor)
        for a, b, norm_factor in itertools.product(A, B, NORM_FACTOR)
    ],
)
def fixture_pulse_distortion(request: pytest.FixtureRequest) -> LFilterCorrection:
    """Fixture for the LFilterCorrection distortion class."""
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


class TestLFilterCorrection:
    """Unit tests checking the LFilterCorrection attributes and methods"""

    def test_apply(self, pulse_distortion: LFilterCorrection, envelope: np.ndarray):
        """Test for the envelope method."""
        norm_factors = [0.90, 0.35]
        corr_envelopes = [pulse_distortion.apply(envelope=envelope)]
        corr_envelopes.append(
            LFilterCorrection(a=[0.7, 1.3], b=[0.5, 0.6], norm_factor=norm_factors[0]).apply(envelope=corr_envelopes[0])
        )
        corr_envelopes.append(
            LFilterCorrection(a=[0.5, 0.6], b=[0.7, 1.3], norm_factor=norm_factors[1]).apply(envelope=corr_envelopes[1])
        )
        not_corr_envelopes = [
            LFilterCorrection(a=[0.1, 0.2, 7.1, 0.2], b=[1.1, 2.2, 1.1, 2.2], auto_norm=False).apply(
                envelope=corr_envelopes[2]
            )
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

    def test_from_dict(self, pulse_distortion: LFilterCorrection):
        """Test for the to_dict method."""
        dictionary = pulse_distortion.to_dict()
        pulse_distortions = [LFilterCorrection.from_dict(dictionary)]

        dictionary.pop(RUNCARD.NAME)
        pulse_distortions.append(LFilterCorrection.from_dict(dictionary))

        dictionary[PulseDistortionSettingsName.A.value] = [0.7, 1.3]
        dictionary[PulseDistortionSettingsName.B.value] = [0.5, 0.6]
        dictionary[PulseDistortionSettingsName.AUTO_NORM.value] = False
        dictionary[PulseDistortionSettingsName.NORM_FACTOR.value] = 1.2
        pulse_distortions.append(LFilterCorrection.from_dict(dictionary))

        for distortion in pulse_distortions:
            assert distortion is not None
            assert isinstance(distortion, LFilterCorrection)

    def test_to_dict(self, pulse_distortion: LFilterCorrection):
        """Test for the to_dict method."""
        dictionary = pulse_distortion.to_dict()

        assert dictionary is not None
        assert isinstance(dictionary, dict)
        assert dictionary == {
            RUNCARD.NAME: pulse_distortion.name.value,
            PulseDistortionSettingsName.A.value: pulse_distortion.a,
            PulseDistortionSettingsName.B.value: pulse_distortion.b,
            PulseDistortionSettingsName.NORM_FACTOR.value: pulse_distortion.norm_factor,
            PulseDistortionSettingsName.AUTO_NORM.value: pulse_distortion.auto_norm,
        }

    def test_serialization(self, pulse_distortion: LFilterCorrection):
        """Test that a serialization of the distortion is possible"""
        dictionary = pulse_distortion.to_dict()
        assert isinstance(dictionary, dict)

        new_pulse_distortion = LFilterCorrection.from_dict(dictionary)
        assert isinstance(new_pulse_distortion, LFilterCorrection)

        new_dictionary = new_pulse_distortion.to_dict()
        assert isinstance(new_dictionary, dict)
        assert new_dictionary == dictionary
