"""Tests for the PulseShape class."""
import itertools
import re

import numpy as np
import pytest

from qililab.pulse.pulse_shape import Cosine, Drag, Gaussian, PulseShape, Rectangular
from qililab.pulse.pulse_shape.snz import SNZ
from qililab.utils import Factory

from .helper_functions import return_envelope

# Parameters of the envelope.
DURATION = [40, 25]
AMPLITUDE = [0, 0.95, -0.8, 1.3]
RESOLUTION = [1.0, 0.2]


@pytest.fixture(
    name="env_params",
    params=[
        {"duration": duration, "amplitude": amplitude, "resolution": resolution}
        for duration, amplitude, resolution in itertools.product(DURATION, AMPLITUDE, RESOLUTION)
    ],
)
def fixture_env_params(request: pytest.FixtureRequest) -> list:
    """Fixture for the envelope parameters."""
    return request.param


@pytest.mark.parametrize(
    "pulse_shape",
    [
        Rectangular(),
        Cosine(),
        Cosine(lambda_2=0.3),
        Gaussian(num_sigmas=4),
        Drag(num_sigmas=4, drag_coefficient=1.0),
    ],
)
class TestPulseShape:
    """Unit tests checking the PulseShape attributes and methods"""

    def test_envelope_methods(self, pulse_shape: PulseShape, env_params: dict[str, int]):
        """Test the envelope method"""
        env = return_envelope(pulse_shape, env_params)

        # Test not None and type
        assert env is not None
        assert isinstance(env, np.ndarray)

        # Assert size of np.ndarray
        assert len(env) == env_params["duration"] / env_params["resolution"]

    def test_max_min_of_envelope_method(self, pulse_shape: PulseShape, env_params: dict[str, int]):
        """Test the maximums and minimums of the envelope method"""
        env = return_envelope(pulse_shape, env_params)

        # Test  the maximums of the positive envelopes
        if env_params["amplitude"] > 0:
            assert round(np.max(np.real(env)), 2) > 0

        # Test the minimums of the negative envelopes
        elif env_params["amplitude"] < 0:
            assert round(np.min(np.real(env)), 2) < 0

        # Test the 0 amplitude case
        elif env_params["amplitude"] == 0:
            assert np.min(np.real(env)) == np.max(np.real(env)) == 0

    def test_from_dict(self, pulse_shape: PulseShape):
        """Test for the to_dict method."""
        dictionary = pulse_shape.to_dict()
        pulse_shape2 = PulseShape.from_dict(dictionary)

        dictionary2 = pulse_shape2.to_dict()
        pulse_shape3 = PulseShape.from_dict(dictionary2)

        for shape in [pulse_shape2, pulse_shape3]:
            assert shape is not None
            assert isinstance(shape, PulseShape)
            assert isinstance(shape, Factory.get(name=pulse_shape.name))

        assert pulse_shape == pulse_shape2 == pulse_shape3

    def test_incorrect_from_dict(self, pulse_shape: PulseShape):
        """Test for the from_dict method with incorrect dictionary."""
        with pytest.raises(ValueError, match=re.escape(f"Class: {Rectangular.name.value} to instantiate, does not match the given dict name {SNZ.name.value}")):
            Rectangular.from_dict({"name": SNZ.name.value})

    def test_to_dict_method(self, pulse_shape: PulseShape):
        """Test to_dict method"""
        dictionary = pulse_shape.to_dict()

        pulse_shape2: PulseShape = Factory.get(name=pulse_shape.name).from_dict(dictionary)
        dictionary2 = pulse_shape2.to_dict()

        for dict_ in [dictionary, dictionary2]:
            assert dict_ is not None
            assert isinstance(dict_, dict)

        assert dictionary2 == dictionary

    def test_envelope_with_amplitude_0(self, pulse_shape):
        """Testing that the corner case amplitude = 0 works properly."""
        ENV_DURATION = 10
        envelope = pulse_shape.envelope(amplitude=0, duration=ENV_DURATION)
        assert np.allclose(envelope, np.zeros(ENV_DURATION))
