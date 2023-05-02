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
TAU_BIAS_TEE = [0.5, 0.9, 1.3]


@pytest.fixture(
    name="distortion",
    params=[BiasTeeCorrection(tau_bias_tee=tau_bias_tee) for tau_bias_tee in TAU_BIAS_TEE],
)
def fixture_distortion(request: pytest.FixtureRequest) -> BiasTeeCorrection:
    """Fixture for the BiasTeeCorrection distortion class."""
    return request.param


class TestBiasTeeCorrection:
    """Unit tests checking the BiasTeeCorrection attributes and methods"""

    def test_apply(self, distortion: BiasTeeCorrection):
        """Test for the envelope method."""
        # Parameters of the Pulse and its envelope.
        AMPLITUDE = [0.9]
        PHASE = [0, np.pi / 3, 2 * np.pi, 3 * np.pi]
        DURATION = [1, 2, 47]  # TODO: Add 0 to this test?
        FREQUENCY = [0.7e9]
        RESOLUTION = [1.1]
        SHAPE = [Rectangular(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, drag_coefficient=1.0)]

        envelopes = []
        corr_envelopes = []

        for amplitude, phase, duration, frequency, resolution, shape in itertools.product(
            AMPLITUDE, PHASE, DURATION, FREQUENCY, RESOLUTION, SHAPE
        ):
            envelope = Pulse(
                amplitude=amplitude, phase=phase, duration=duration, frequency=frequency, pulse_shape=shape
            ).envelope(resolution=resolution)
            envelopes.append(envelope)

        for counter, envelope in enumerate(envelopes):
            corr_envelopes.append(distortion.apply(envelope=envelope))
            corr_envelopes.append(BiasTeeCorrection(tau_bias_tee=1.3).apply(envelope=corr_envelopes[0 + counter * 4]))
            corr_envelopes.append(BiasTeeCorrection(tau_bias_tee=0.5).apply(envelope=corr_envelopes[1 + counter * 4]))
            corr_envelopes.append(BiasTeeCorrection(tau_bias_tee=0.5).apply(envelope=corr_envelopes[1 + counter * 4]))

        for corr_envelope in corr_envelopes:
            assert corr_envelope is not None
            assert isinstance(corr_envelope, np.ndarray)

    def test_to_dict(self, distortion: BiasTeeCorrection):
        """Test for the to_dict method."""

        dictionary = distortion.to_dict()
        assert dictionary is not None
        assert isinstance(dictionary, dict)
        assert list(dictionary.keys()) == [
            RUNCARD.NAME,
            PulseDistortionSettingsName.TAU_BIAS_TEE.value,
        ]
