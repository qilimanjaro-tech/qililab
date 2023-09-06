"""Tests for the LFilterCorrection distortion class."""
import itertools

import numpy as np
import pytest

from qililab.pulse import Pulse
from qililab.pulse.pulse_distortion import LFilterCorrection
from qililab.pulse.pulse_shape import SNZ, Cosine, Drag, Gaussian, Rectangular

# Parameters for the LFilterCorrection.
NORM_FACTOR = [1.0]
A = [[0.7, 1.3], [0.8, 0.6]]
B = [[0.5, 0.6], [0.8, 1.3]]


# Parameters of the Pulse and its envelope.
AMPLITUDE = [0, 0.9, -0.7, 2.1]
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
    """Fixture for an envelope."""
    return request.param


def return_corrected_envelopes_examples(
    pulse_distortion: LFilterCorrection, envelope: np.ndarray, norm_factors: list[float]
):
    """Helper function that returns examples of envelopes with & without auto_norm"""
    norm_corr_envelopes = [pulse_distortion.apply(envelope=envelope)]
    norm_corr_envelopes.append(
        LFilterCorrection(a=[0.7, 1.3], b=[0.5, 0.6], norm_factor=norm_factors[0]).apply(
            envelope=norm_corr_envelopes[0]
        )
    )
    norm_corr_envelopes.append(
        LFilterCorrection(a=[0.5, 0.6], b=[0.7, 1.3], norm_factor=norm_factors[1]).apply(
            envelope=norm_corr_envelopes[1]
        )
    )
    not_norm_corr_envelopes = [
        LFilterCorrection(a=[0.1, 0.2, 7.1, 0.2], b=[1.1, 2.2, 1.1, 2.2], auto_norm=False).apply(
            envelope=norm_corr_envelopes[2]
        )
    ]
    not_norm_corr_envelopes.append(
        LFilterCorrection(a=[0.1, 0.2, 3.1, 0.1], b=[1.1, 4.2, 1.1, 2.2], auto_norm=False).apply(
            envelope=not_norm_corr_envelopes[0]
        )
    )
    return norm_corr_envelopes, not_norm_corr_envelopes


class TestLFilterCorrection:
    """Unit tests checking the LFilterCorrection attributes and methods"""

    def test_apply(self, pulse_distortion: LFilterCorrection, envelope: np.ndarray):
        """Test for the envelope method."""
        norm_factors = [0.90, 0.35]
        norm_corr_envelopes, not_norm_corr_envelopes = return_corrected_envelopes_examples(
            pulse_distortion, envelope, norm_factors
        )

        # Basic checks
        for corr_envelope in norm_corr_envelopes + not_norm_corr_envelopes:
            assert corr_envelope is not None
            assert isinstance(corr_envelope, np.ndarray)
            assert len(envelope) == len(corr_envelope)
            assert (
                not np.array_equal(corr_envelope, envelope)
                or np.max(np.abs(np.real(envelope))) == np.max(np.abs(np.real(corr_envelope))) == 0.0
            )

        # Check that norm_factor and auto_norm is working properly
        assert (
            0.0  # Testing/Discarting the amplitude = 0 cases, for both maxs and mins.
            == round(np.max(np.abs(np.real(envelope))), 13)
            == round(np.min(np.abs(np.real(envelope))), 13)
            == round(np.max(np.abs(np.real(norm_corr_envelopes[0]))), 13)
            == round(np.min(np.abs(np.real(norm_corr_envelopes[0]))), 13)
            == round(np.max(np.abs(np.real(norm_corr_envelopes[1]))), 13)
            == round(np.min(np.abs(np.real(norm_corr_envelopes[1]))), 13)
            == round(np.max(np.abs(np.real(norm_corr_envelopes[2]))), 13)
            == round(np.min(np.abs(np.real(norm_corr_envelopes[2]))), 13)
            == round(np.max(np.abs(np.real(not_norm_corr_envelopes[0]))), 13)
            == round(np.min(np.abs(np.real(not_norm_corr_envelopes[0]))), 13)
            == round(np.max(np.abs(np.real(not_norm_corr_envelopes[1]))), 13)
            == round(np.min(np.abs(np.real(not_norm_corr_envelopes[1]))), 13)
        ) or (
            # Actual testing that the norm_factors are working properly, the factors
            # should correspond to the ones in the function "return_corrected_envelopes_examples()"
            round(np.max(np.abs(np.real(norm_corr_envelopes[0]))), 14)
            == round(np.max(np.abs(np.real(norm_corr_envelopes[1]))) / norm_factors[0], 14)
            == round(np.max(np.abs(np.real(norm_corr_envelopes[2]))) / (norm_factors[0] * norm_factors[1]), 14)
            == round(np.max(np.abs(np.real(envelope))) * pulse_distortion.norm_factor, 14)
            # Testing that the auto_norm changes the norm from the previous
            != round(np.max(np.abs(np.real(not_norm_corr_envelopes[0]))) / (norm_factors[0] * norm_factors[1]), 14)
            # The next one has auto_norm = False again, so it has to be different again.
            != round(np.max(np.abs(np.real(not_norm_corr_envelopes[1]))) / (norm_factors[0] * norm_factors[1]), 14)
        )

    def test_from_dict(self, pulse_distortion: LFilterCorrection):
        """Test for the to_dict method."""
        dictionary = pulse_distortion.to_dict()
        pulse_distortions = [LFilterCorrection.from_dict(dictionary)]

        dictionary.pop("name")
        pulse_distortions.append(LFilterCorrection.from_dict(dictionary))

        dictionary["a"] = [0.7, 1.3]
        dictionary["b"] = [0.5, 0.6]
        dictionary["auto_norm"] = False
        dictionary["norm_factor"] = 1.2
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
            "name": pulse_distortion.name.value,
            "a": pulse_distortion.a,
            "b": pulse_distortion.b,
            "norm_factor": pulse_distortion.norm_factor,
            "auto_norm": pulse_distortion.auto_norm,
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
