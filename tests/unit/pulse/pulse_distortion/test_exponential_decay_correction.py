"""Tests for the ExponentialCorrection distortion class."""
import itertools

import numpy as np
import pytest

from qililab.constants import RUNCARD
from qililab.pulse import Pulse
from qililab.pulse.pulse_distortion import ExponentialCorrection
from qililab.pulse.pulse_shape import Drag, Gaussian, Rectangular
from qililab.typings.enums import PulseDistortionSettingsName

# Parameters for the ExponentialCorrection.
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
    name="distortion",
    params=[
        ExponentialCorrection(tau_exponential=tau_exponential, amp=amp)
        for tau_exponential, amp in itertools.product(TAU_EXPONENTIAL, AMP)
    ],
)
def fixture_distortion(request: pytest.FixtureRequest) -> ExponentialCorrection:
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

    def test_apply(self, distortion: ExponentialCorrection, envelope: np.ndarray):
        """Test for the envelope method."""
        corr_envelopes = [distortion.apply(envelope=envelope)]
        corr_envelopes.append(ExponentialCorrection(tau_exponential=1.3, amp=2.0).apply(envelope=corr_envelopes[0]))
        corr_envelopes.append(ExponentialCorrection(tau_exponential=0.5, amp=-5.0).apply(envelope=corr_envelopes[1]))
        corr_envelopes.append(ExponentialCorrection(tau_exponential=0.5, amp=-5.0).apply(envelope=corr_envelopes[1]))

        for corr_envelope in corr_envelopes:
            assert corr_envelope is not None
            assert isinstance(corr_envelope, np.ndarray)

    def test_from_dict(self, distortion: ExponentialCorrection):
        """Test for the to_dict method."""
        dictionary = distortion.to_dict()
        distortions = [ExponentialCorrection.from_dict(dictionary)]

        dictionary.pop(PulseDistortionSettingsName.SAMPLING_RATE.value)
        distortions.append(ExponentialCorrection.from_dict(dictionary))

        dictionary.pop(RUNCARD.NAME)
        distortions.append(ExponentialCorrection.from_dict(dictionary))

        dictionary[PulseDistortionSettingsName.TAU_EXPONENTIAL.value] = 0.5
        dictionary[PulseDistortionSettingsName.AMP.value] = 1.2
        dictionary[PulseDistortionSettingsName.SAMPLING_RATE.value] = 2.0
        distortions.append(ExponentialCorrection.from_dict(dictionary))

        for distortion in distortions:
            assert distortion is not None
            assert isinstance(distortion, ExponentialCorrection)

    def test_to_dict(self, distortion: ExponentialCorrection):
        """Test for the to_dict method."""
        dictionary = distortion.to_dict()

        assert dictionary is not None
        assert isinstance(dictionary, dict)
        assert dictionary == {
            RUNCARD.NAME: distortion.name.value,
            PulseDistortionSettingsName.TAU_EXPONENTIAL.value: distortion.tau_exponential,
            PulseDistortionSettingsName.AMP.value: distortion.amp,
            PulseDistortionSettingsName.SAMPLING_RATE.value: distortion.sampling_rate,
        }
