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

# Parameters for the different corrections.
TAU_BIAS_TEE = [0.5, 0.9, 1.3]
TAU_EXPONENTIAL = [0.5, 0.9, 1.3]
AMP = [-5.1, 1.2, 0.8, 2.0]


@pytest.fixture(
    name="distortion",
    params=[
        ExponentialCorrection(tau_exponential=tau_exponential, amp=amp)
        for tau_exponential, amp in itertools.product(TAU_EXPONENTIAL, AMP)
    ]
    + [BiasTeeCorrection(tau_bias_tee=tau_bias_tee) for tau_bias_tee in TAU_BIAS_TEE],
)
def fixture_distortion(request: pytest.FixtureRequest) -> ExponentialCorrection:
    """Fixture for the pulse distortion class."""
    return request.param


class TestPulseDistortion:
    """Unit tests checking the PulseDistortion attributes and methods"""

    def test_apply(self, distortion: PulseDistortion):
        """Test for the apply method."""
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
            corr_envelopes.append(
                ExponentialCorrection(tau_exponential=1.3, amp=2.0).apply(envelope=corr_envelopes[0 + counter * 4])
            )
            corr_envelopes.append(BiasTeeCorrection(tau_bias_tee=0.5).apply(envelope=corr_envelopes[1 + counter * 4]))
            corr_envelopes.append(
                ExponentialCorrection(tau_exponential=0.5, amp=-5.0).apply(envelope=corr_envelopes[1 + counter * 4])
            )

        for corr_envelope in corr_envelopes:
            assert corr_envelope is not None
            assert isinstance(corr_envelope, np.ndarray)

    def test_from_dict(self, distortion: PulseDistortion):
        """Test for the to_dict method."""
        dictionary = distortion.to_dict()
        distortion2: PulseDistortion

        if isinstance(distortion, BiasTeeCorrection):
            distortion2 = BiasTeeCorrection.from_dict(dictionary)
            assert isinstance(distortion2, BiasTeeCorrection)

        if isinstance(distortion, ExponentialCorrection):
            distortion2 = ExponentialCorrection.from_dict(dictionary)
            assert isinstance(distortion2, ExponentialCorrection)

        assert distortion2 is not None
        assert isinstance(distortion2, PulseDistortion)

    def test_to_dict(self, distortion: PulseDistortion):
        """Test for the to_dict method."""
        dictionary = distortion.to_dict()

        assert dictionary is not None
        assert isinstance(dictionary, dict)

        if isinstance(distortion, BiasTeeCorrection):
            assert dictionary == {
                RUNCARD.NAME: distortion.name.value,
                PulseDistortionSettingsName.TAU_BIAS_TEE.value: distortion.tau_bias_tee,
                PulseDistortionSettingsName.SAMPLING_RATE.value: distortion.sampling_rate,
            }

        if isinstance(distortion, ExponentialCorrection):
            assert dictionary == {
                RUNCARD.NAME: distortion.name.value,
                PulseDistortionSettingsName.TAU_EXPONENTIAL.value: distortion.tau_exponential,
                PulseDistortionSettingsName.AMP.value: distortion.amp,
                PulseDistortionSettingsName.SAMPLING_RATE.value: distortion.sampling_rate,
            }
