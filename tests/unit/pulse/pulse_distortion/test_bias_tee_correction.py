"""Tests for the BiasTeeCorrection distortion class."""
import itertools

import numpy as np
import pytest

from qililab.constants import RUNCARD
from qililab.pulse import Pulse
from qililab.pulse.pulse_distortion import BiasTeeCorrection
from qililab.pulse.pulse_shape import Drag, Gaussian, Rectangular
from qililab.typings.enums import PulseDistortionSettingsName

# Parameters for the BiasTeeCorrection.
TAU_BIAS_TEE = [0.7, 1.3]

# Parameters of the Pulse and its envelope.
AMPLITUDE = [0.9]
PHASE = [0, np.pi / 3, 2 * np.pi]
DURATION = [47]
FREQUENCY = [0.7e9]
RESOLUTION = [1.1]
SHAPE = [Rectangular(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, drag_coefficient=1.0)]


@pytest.fixture(
    name="distortion",
    params=[BiasTeeCorrection(tau_bias_tee=tau_bias_tee) for tau_bias_tee in TAU_BIAS_TEE],
)
def fixture_distortion(request: pytest.FixtureRequest) -> BiasTeeCorrection:
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

    def test_apply(self, distortion: BiasTeeCorrection, envelope: np.ndarray):
        """Test for the envelope method."""
        corr_envelopes = [distortion.apply(envelope=envelope)]
        corr_envelopes.append(BiasTeeCorrection(tau_bias_tee=1.3).apply(envelope=corr_envelopes[0]))
        corr_envelopes.append(BiasTeeCorrection(tau_bias_tee=0.5).apply(envelope=corr_envelopes[1]))
        corr_envelopes.append(BiasTeeCorrection(tau_bias_tee=0.5).apply(envelope=corr_envelopes[1]))

        for corr_envelope in corr_envelopes:
            assert corr_envelope is not None
            assert isinstance(corr_envelope, np.ndarray)
            assert len(envelope) == len(corr_envelope)
            assert round(np.max(np.abs(corr_envelope)), 14) == round(np.max(np.abs(envelope)), 14)
            assert not np.array_equal(corr_envelope, envelope)

    def test_from_dict(self, distortion: BiasTeeCorrection):
        """Test for the to_dict method."""
        dictionary = distortion.to_dict()
        distortions = [BiasTeeCorrection.from_dict(dictionary)]

        dictionary.pop(PulseDistortionSettingsName.SAMPLING_RATE.value)
        distortions.append(BiasTeeCorrection.from_dict(dictionary))

        dictionary.pop(RUNCARD.NAME)
        distortions.append(BiasTeeCorrection.from_dict(dictionary))

        dictionary[PulseDistortionSettingsName.TAU_BIAS_TEE.value] = 0.5
        dictionary[PulseDistortionSettingsName.SAMPLING_RATE.value] = 2.0
        distortions.append(BiasTeeCorrection.from_dict(dictionary))

        for distortion in distortions:
            assert distortion is not None
            assert isinstance(distortion, BiasTeeCorrection)

    def test_to_dict(self, distortion: BiasTeeCorrection):
        """Test for the to_dict method."""
        dictionary = distortion.to_dict()

        assert dictionary is not None
        assert isinstance(dictionary, dict)
        assert dictionary == {
            RUNCARD.NAME: distortion.name.value,
            PulseDistortionSettingsName.TAU_BIAS_TEE.value: distortion.tau_bias_tee,
            PulseDistortionSettingsName.SAMPLING_RATE.value: distortion.sampling_rate,
        }
