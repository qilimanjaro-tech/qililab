"""Tests for the BiasTeeCorrection distortion class."""
import itertools

import numpy as np
import pytest

from qililab.constants import RUNCARD
from qililab.pulse import Pulse
from qililab.pulse.pulse_distortion import LFilter
from qililab.pulse.pulse_shape import Drag, Gaussian, Rectangular
from qililab.typings.enums import PulseDistortionSettingsName

# Parameters for the BiasTeeCorrection.
NORMALIZATION_FACTOR = [1.0, 2.0]
A = [[0.7, 1.3], [0.5, 0.6]]
B = [[0.5, 0.6], [0.7, 1.3]]

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
        LFilter(norm_factor=norm_factor, a=a, b=b)
        for norm_factor, a, b, in itertools.product(NORMALIZATION_FACTOR, A, B)
    ],
)
def fixture_pulse_distortion(request: pytest.FixtureRequest) -> LFilter:
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

    def test_apply(self, pulse_distortion: LFilter, envelope: np.ndarray):
        """Test for the envelope method."""
        corr_envelopes = [pulse_distortion.apply(envelope=envelope)]
        corr_envelopes.append(LFilter(norm_factor=1.0, a=[0.7, 1.3], b=[0.5, 0.6]).apply(envelope=corr_envelopes[0]))
        corr_envelopes.append(LFilter(norm_factor=2.3, a=[0.5, 0.6], b=[0.7, 1.3]).apply(envelope=corr_envelopes[1]))
        corr_envelopes.append(LFilter(norm_factor=1.2, a=[0.7, 1.3], b=[0.5, 0.6]).apply(envelope=corr_envelopes[2]))

        for corr_envelope in corr_envelopes:
            assert corr_envelope is not None
            assert isinstance(corr_envelope, np.ndarray)
            assert len(envelope) == len(corr_envelope)
            assert round(np.max(np.real(corr_envelope)), 14) == round(
                np.max(np.real(envelope)), 14
            )  # This should fail unless all norm_factor = 1.0
            assert not np.array_equal(corr_envelope, envelope)

    def test_from_dict(self, pulse_distortion: LFilter):
        """Test for the to_dict method."""
        dictionary = pulse_distortion.to_dict()
        pulse_distortions = [LFilter.from_dict(dictionary)]

        dictionary.pop(RUNCARD.NAME)
        pulse_distortions.append(LFilter.from_dict(dictionary))

        dictionary[PulseDistortionSettingsName.NORMALIZATION_FACTOR.value] = 1.2
        dictionary[PulseDistortionSettingsName.A.value] = [0.7, 1.3]
        dictionary[PulseDistortionSettingsName.B.value] = [0.5, 0.6]
        pulse_distortions.append(LFilter.from_dict(dictionary))

        for distortion in pulse_distortions:
            assert distortion is not None
            assert isinstance(distortion, LFilter)

    def test_to_dict(self, pulse_distortion: LFilter):
        """Test for the to_dict method."""
        dictionary = pulse_distortion.to_dict()

        assert dictionary is not None
        assert isinstance(dictionary, dict)
        assert dictionary == {
            RUNCARD.NAME: pulse_distortion.name.value,
            PulseDistortionSettingsName.NORMALIZATION_FACTOR.value: pulse_distortion.norm_factor,
            PulseDistortionSettingsName.A.value: pulse_distortion.a,
            PulseDistortionSettingsName.B.value: pulse_distortion.b,
        }
