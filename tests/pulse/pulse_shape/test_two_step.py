"""Tests for the PulseShape class."""

import itertools

import numpy as np
import pytest

from qililab.pulse.pulse_shape import PulseShape, TwoStep

from .helper_functions import return_envelope

# Parameters of the envelope.
DURATION = [500]
AMPLITUDE = [1.2]
RESOLUTION = [1.0]
BUFFER = [2.0]


@pytest.fixture(
    name="env_params",
    params=[
        {"duration": duration, "amplitude": amplitude, "resolution": resolution, "buffer": buffer}
        for duration, amplitude, resolution, buffer in itertools.product(DURATION, AMPLITUDE, RESOLUTION, BUFFER)
    ],
)
def fixture_env_params(request: pytest.FixtureRequest) -> list:
    """Fixture for the envelope parameters."""
    return request.param


@pytest.mark.parametrize("pulse_shape", [TwoStep(step_amplitude=1, step_duration=5)])
class TestPulseShape:
    """Unit tests checking the PulseShape attributes and methods"""

    def test_envelope_methods(self, pulse_shape: TwoStep, env_params: dict[str, int]):
        """Test the envelope method"""
        env = return_envelope(pulse_shape, env_params)

        # Test not None and type
        assert env is not None
        assert isinstance(env, np.ndarray)

        # Assert size of np.ndarray
        assert len(env) == env_params["duration"] / env_params["resolution"]
        envelope = np.concatenate(
            (
                env_params["amplitude"] * np.ones(pulse_shape.step_duration),
                pulse_shape.step_amplitude * np.ones(env_params["duration"] - pulse_shape.step_duration),
            )
        )
        assert np.allclose(env, envelope)

    def test_max_min_of_envelope_method(self, pulse_shape: TwoStep, env_params: dict[str, int]):
        """Test the maximums and minimums of the envelope method"""
        env = return_envelope(pulse_shape, env_params)

        # Test  the maximums of the positive envelopes
        if env_params["amplitude"] > 0:
            assert round(np.max(np.real(env)), 2) == np.max(env_params["amplitude"])

        # Test the minimums of the negative envelopes
        elif env_params["amplitude"] < 0:
            assert round(np.min(np.real(env)), 2) == np.min(env_params["amplitude"])

        # Test the 0 amplitude case
        elif env_params["amplitude"] == 0:
            assert np.min(np.real(env)) == np.max(np.real(env)) == 0

    def test_envelope_method_shapes(self, pulse_shape: TwoStep, env_params: dict[str, int]):
        """Test shapes of the envelopes"""
        env = return_envelope(pulse_shape, env_params)

        # positive amplitude cases
        if env_params["amplitude"] > 0 or env_params["amplitude"] < 0:
            assert env[0] == env[pulse_shape.step_duration - 1]
            assert env[pulse_shape.step_duration] == env[-1]

        elif env_params["amplitude"] == 0:
            assert np.min(env) == 0

    def test_from_dict(self, pulse_shape: TwoStep):
        """Test for the to_dict method."""
        dictionary = pulse_shape.to_dict()
        pulse_shape2: TwoStep = TwoStep.from_dict(dictionary)

        dictionary2 = pulse_shape2.to_dict()
        pulse_shape3: TwoStep = TwoStep.from_dict(dictionary2)

        for shape in [pulse_shape2, pulse_shape3]:
            assert shape is not None
            assert isinstance(shape, PulseShape)
            assert isinstance(shape, TwoStep)

        assert pulse_shape == pulse_shape2 == pulse_shape3

    def test_to_dict_method(self, pulse_shape: TwoStep):
        """Test to_dict method"""
        dictionary = pulse_shape.to_dict()

        pulse_shape2: TwoStep = TwoStep.from_dict(dictionary)
        dictionary2 = pulse_shape2.to_dict()

        for dict_ in [dictionary, dictionary2]:
            assert dict_ is not None
            assert isinstance(dict_, dict)

        assert (
            dictionary
            == dictionary2
            == {
                "name": pulse_shape.name.value,  # type: ignore[operator]
                "step_amplitude": pulse_shape.step_amplitude,
                "step_duration": pulse_shape.step_duration,
            }
        )

    def test_envelope_with_amplitude_0(self, pulse_shape: TwoStep):
        """Testing that the corner case amplitude = 0 works properly."""
        ENV_DURATION = 10
        envelope = pulse_shape.envelope(amplitude=0, duration=ENV_DURATION)
        assert np.allclose(envelope, [0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
