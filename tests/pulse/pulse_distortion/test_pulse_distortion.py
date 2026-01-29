"""Tests for the pulse distortion class."""
import itertools
import re

import numpy as np
import pytest

from qililab.pulse import Pulse
from qililab.pulse.pulse_distortion import BiasTeeCorrection, ExponentialCorrection, LFilterCorrection
from qililab.pulse.pulse_distortion.pulse_distortion import PulseDistortion
from qililab.pulse.pulse_shape import Cosine, Drag, Gaussian, Rectangular
from qililab.utils import Factory

# Parameters for the different corrections.
NORM_FACTOR = [0.95]
TAU_BIAS_TEE = [0.6]
TAU_EXPONENTIAL = [0.7]
AMP = [-2.1, 0.8]
A = [[0.7, 1.3]]
B = [[0.5, 0.6]]

# Parameters of the Pulse and its envelope.
AMPLITUDE = [-0.8, 0.9, 0]
PHASE = [0, np.pi / 3]
DURATION = [50, 37]  # Since we don't have the SNZ in this test, we can try an odd duration here.
FREQUENCY = [0.7e9]
RESOLUTION = [1.0]
SHAPE = [
    Rectangular(),
    Cosine(),
    Cosine(lambda_2=0.3),
    Gaussian(num_sigmas=4),
    Drag(num_sigmas=4, drag_coefficient=1.0),
]


@pytest.fixture(
    name="pulse_distortion",
    params=[
        ExponentialCorrection(tau_exponential=tau_exponential, amp=amp, norm_factor=norm_factor)
        for tau_exponential, amp, norm_factor in itertools.product(TAU_EXPONENTIAL, AMP, NORM_FACTOR)
    ]
    + [BiasTeeCorrection(tau_bias_tee=tau_bias_tee) for tau_bias_tee in TAU_BIAS_TEE]
    + [
        LFilterCorrection(a=a, b=b, norm_factor=norm_factor)
        for a, b, norm_factor in itertools.product(A, B, NORM_FACTOR)
    ],
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
    """Fixture for an envelope."""
    return request.param


def return_corrected_envelopes_examples(
    pulse_distortion: PulseDistortion, envelope: np.ndarray, norm_factors: list[float]
):
    """Helper function that returns examples of envelopes with & without auto_norm"""
    norm_corr_envelopes = [pulse_distortion.apply(envelope=envelope)]
    norm_corr_envelopes.append(
        ExponentialCorrection(tau_exponential=1.3, amp=2.0, norm_factor=norm_factors[0]).apply(
            envelope=norm_corr_envelopes[0]
        )
    )
    norm_corr_envelopes.append(
        BiasTeeCorrection(tau_bias_tee=0.5, norm_factor=norm_factors[1]).apply(envelope=norm_corr_envelopes[1])
    )
    not_norm_corr_envelopes = [
        ExponentialCorrection(tau_exponential=0.5, amp=-5.0, auto_norm=False, norm_factor=norm_factors[1]).apply(
            envelope=norm_corr_envelopes[1]
        )
    ]
    not_norm_corr_envelopes.append(
        LFilterCorrection(a=[0.7, 1.3], b=[0.5, 0.6], norm_factor=norm_factors[0]).apply(
            envelope=not_norm_corr_envelopes[0]
        )
    )
    return norm_corr_envelopes, not_norm_corr_envelopes


class TestPulseDistortion:
    """Unit tests checking the PulseDistortion attributes and methods"""

    def test_apply_method(self, pulse_distortion: PulseDistortion, envelope: np.ndarray):
        """Test for the apply method."""
        norm_factors = [0.8, 1.15]
        norm_corr_envelopes, not_norm_corr_envelopes = return_corrected_envelopes_examples(
            pulse_distortion, envelope, norm_factors
        )

        # Basic checks
        for corr_envelope in norm_corr_envelopes + not_norm_corr_envelopes:
            assert corr_envelope is not None
            assert isinstance(envelope, np.ndarray)
            assert len(envelope) == len(corr_envelope)
            assert (
                not np.array_equal(envelope, corr_envelope)
                # Discarting the ampltidue = 0 case
                or np.max(np.abs(np.real(envelope))) == np.max(np.abs(np.real(corr_envelope))) == 0.0
            )

        # Autonorm = True cases, with amplitudes and norm_factors <= 1, have to return an envelope between -1 and 1:
        for norm_corr_envelope in norm_corr_envelopes:
            assert np.max((np.real(norm_corr_envelope))) <= 1
            assert np.min((np.real(norm_corr_envelope))) >= -1

    def test_norm_factors_and_auto_norm_in_apply_method(self, pulse_distortion: PulseDistortion, envelope: np.ndarray):
        """Test for the apply method."""
        norm_factors = [1.8, 0.35, 0.8]
        norm_corr_envelopes, not_norm_corr_envelopes = return_corrected_envelopes_examples(
            pulse_distortion, envelope, norm_factors
        )

        # Both Auto-norm = True & False, and Norm factors > 1 included
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
            round(np.max(np.abs(np.real(norm_corr_envelopes[0]))), 13)
            == round(np.max(np.abs(np.real(norm_corr_envelopes[1]))) / norm_factors[0], 13)
            == round(np.max(np.abs(np.real(norm_corr_envelopes[2]))) / (norm_factors[0] * norm_factors[1]), 13)
            == round(np.max(np.abs(np.real(envelope))) * pulse_distortion.norm_factor, 13)
            # Testing that the auto_norm changes the norm from the previous
            != round(np.max(np.abs(np.real(not_norm_corr_envelopes[0]))) / (norm_factors[0] * norm_factors[1]), 2)
            # Then we get back to a case with auto_norm = True, so we can check it again.
            == round(np.max(np.abs(np.real(not_norm_corr_envelopes[1]))) / (norm_factors[0] ** 2 * norm_factors[1]), 2)
        )

    def test_from_dict(self, pulse_distortion: PulseDistortion):
        """Test for the to_dict method."""
        dictionary = pulse_distortion.to_dict()
        pulse_distortion2 = PulseDistortion.from_dict(dictionary)

        dictionary2 = pulse_distortion2.to_dict()
        pulse_distortion3 = PulseDistortion.from_dict(dictionary2)

        assert isinstance(pulse_distortion2, Factory.get(name=pulse_distortion.name))
        assert isinstance(pulse_distortion3, Factory.get(name=pulse_distortion2.name))
        assert pulse_distortion2 is not None and pulse_distortion3 is not None
        assert isinstance(pulse_distortion2, PulseDistortion) and isinstance(pulse_distortion3, PulseDistortion)
        assert pulse_distortion == pulse_distortion2 == pulse_distortion3

    def test_incorrect_from_dict(self):
        """Test for the from_dict method with incorrect dictionary."""
        with pytest.raises(ValueError, match=re.escape(f"Class: {BiasTeeCorrection.name.value} to instantiate, does not match the given dict name {LFilterCorrection.name.value}")):
            BiasTeeCorrection.from_dict({"name": LFilterCorrection.name.value})

    def test_to_dict(self, pulse_distortion: PulseDistortion):
        """Test for the to_dict method."""
        dictionary = pulse_distortion.to_dict()

        assert dictionary is not None
        assert isinstance(dictionary, dict)

        if isinstance(pulse_distortion, BiasTeeCorrection):
            assert dictionary == {
                "name": pulse_distortion.name.value,
                "tau_bias_tee": pulse_distortion.tau_bias_tee,
                "sampling_rate": pulse_distortion.sampling_rate,
                "norm_factor": pulse_distortion.norm_factor,
                "auto_norm": pulse_distortion.auto_norm,
            }

        if isinstance(pulse_distortion, ExponentialCorrection):
            assert dictionary == {
                "name": pulse_distortion.name.value,
                "tau_exponential": pulse_distortion.tau_exponential,
                "amp": pulse_distortion.amp,
                "sampling_rate": pulse_distortion.sampling_rate,
                "norm_factor": pulse_distortion.norm_factor,
                "auto_norm": pulse_distortion.auto_norm,
            }

        if isinstance(pulse_distortion, LFilterCorrection):
            assert dictionary == {
                "name": pulse_distortion.name.value,
                "a": pulse_distortion.a,
                "b": pulse_distortion.b,
                "norm_factor": pulse_distortion.norm_factor,
                "auto_norm": pulse_distortion.auto_norm,
            }

    # TESTING CORNER CASES:

    @pytest.mark.parametrize(
        "envelope",
        [
            Rectangular().envelope(amplitude=0, duration=DURATION[1]),
            Rectangular().envelope(amplitude=0, duration=DURATION[0]),
            Cosine().envelope(amplitude=0, duration=DURATION[0]),
            Cosine(lambda_2=0.3).envelope(amplitude=0, duration=DURATION[0]),
            Gaussian(num_sigmas=4).envelope(amplitude=0, duration=DURATION[0]),
            Drag(num_sigmas=4, drag_coefficient=1.0).envelope(amplitude=0, duration=DURATION[0]),
        ],
    )
    def test_envelope_with_amplitude_0(self, pulse_distortion, envelope):
        """Testing that the corner case amplitude = 0 works properly."""
        corr_envelope = pulse_distortion.apply(envelope)
        assert 0.0 == np.max(np.abs(np.real(corr_envelope))) == np.min(np.abs(np.real(corr_envelope)))

    BIG_AMPLITUDES = [2.0, 1.2, -2.0]

    @pytest.mark.parametrize(
        "envelope",
        [
            Rectangular().envelope(amplitude=BIG_AMPLITUDES[0], duration=DURATION[1]),
            Rectangular().envelope(amplitude=BIG_AMPLITUDES[1], duration=DURATION[0]),
            Rectangular().envelope(amplitude=BIG_AMPLITUDES[2], duration=DURATION[0]),
            Cosine().envelope(amplitude=BIG_AMPLITUDES[1], duration=DURATION[0]),
            Cosine().envelope(amplitude=BIG_AMPLITUDES[2], duration=DURATION[1]),
            Cosine(lambda_2=0.3).envelope(amplitude=BIG_AMPLITUDES[1], duration=DURATION[0]),
            Gaussian(num_sigmas=4).envelope(amplitude=BIG_AMPLITUDES[1], duration=DURATION[0]),
            Drag(num_sigmas=4, drag_coefficient=1.0).envelope(amplitude=BIG_AMPLITUDES[1], duration=DURATION[0]),
        ],
    )
    def test_envelope_with_amplitude_bigger_than_1(self, pulse_distortion, envelope):
        """Testing that the corner case amplitude > 1 works properly."""
        assert np.max(np.abs(np.real(envelope))) > 1 or np.min(np.abs(np.real(envelope))) < 1

        corr_envelope = pulse_distortion.apply(envelope)
        assert np.max(np.abs(np.real(corr_envelope))) > 1 or np.min(np.abs(np.real(corr_envelope))) < 1
