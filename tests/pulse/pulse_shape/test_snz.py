"""Tests for the PulseShape class."""

import itertools

import numpy as np
import pytest

from qililab.pulse.pulse_shape import SNZ, PulseShape

from .helper_functions import return_envelope

# Parameters of the envelope.
DURATION = [50, 40, 500]
AMPLITUDE = [0, 0.9, -1.0, 1.2]
RESOLUTION = [1.0]


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


@pytest.mark.parametrize("pulse_shape", [SNZ(b=0.1, t_phi=2), SNZ(b=0.2, t_phi=4)])
class TestPulseShape:
    """Unit tests checking the PulseShape attributes and methods"""

    def test_envelope_methods(self, pulse_shape: SNZ, env_params: dict[str, int]):
        """Test the envelope method"""
        env = return_envelope(pulse_shape, env_params)

        # Test not None and type
        assert env is not None
        assert isinstance(env, np.ndarray)

        # Assert size of np.ndarray
        assert len(env) == env_params["duration"] / env_params["resolution"]

    def test_max_min_of_envelope_method(self, pulse_shape: SNZ, env_params: dict[str, int]):
        """Test the maximums and minimums of the envelope method"""
        env = return_envelope(pulse_shape, env_params)

        # Test  the maximums of the positive envelopes
        if env_params["amplitude"] > 0:
            assert round(np.max(np.real(env)), 2) == np.max(env_params["amplitude"])
            assert round(np.max(np.real(env)), 2) > 0

        # Test the minimums of the negative envelopes
        elif env_params["amplitude"] < 0:
            assert round(np.min(np.real(env)), 2) == np.min(env_params["amplitude"])
            assert round(np.min(np.real(env)), 2) < 0

        # Test the 0 amplitude case
        elif env_params["amplitude"] == 0:
            assert np.min(np.real(env)) == np.max(np.real(env)) == 0

    def test_envelope_method_shapes(self, pulse_shape: SNZ, env_params: dict[str, int]):
        """Test shapes of the envelopes"""
        env = return_envelope(pulse_shape, env_params)

        # positive amplitude cases
        if env_params["amplitude"] > 0 or env_params["amplitude"] < 0:
            assert np.max(env) == -np.min(env)
            assert env[len(env) // 2] == 0

        elif env_params["amplitude"] == 0:
            assert np.min(np.real(env)) == np.max(np.real(env)) == 0

    def test_from_dict(self, pulse_shape: SNZ):
        """Test for the to_dict method."""
        dictionary = pulse_shape.to_dict()
        pulse_shape2: SNZ = SNZ.from_dict(dictionary)

        dictionary2 = pulse_shape2.to_dict()
        pulse_shape3: SNZ = SNZ.from_dict(dictionary2)

        for shape in [pulse_shape2, pulse_shape3]:
            assert shape is not None
            assert isinstance(shape, PulseShape)
            assert isinstance(shape, SNZ)

        assert pulse_shape == pulse_shape2 == pulse_shape3

    def test_to_dict_method(self, pulse_shape: SNZ):
        """Test to_dict method"""
        dictionary = pulse_shape.to_dict()

        pulse_shape2: SNZ = SNZ.from_dict(dictionary)
        dictionary2 = pulse_shape2.to_dict()

        for dict_ in [dictionary, dictionary2]:
            assert dict_ is not None
            assert isinstance(dict_, dict)

        assert (
            dictionary
            == dictionary2
            == {
                "name": pulse_shape.name.value,  # type: ignore[operator]
                "b": pulse_shape.b,
                "t_phi": pulse_shape.t_phi,
            }
        )

    def test_envelope_with_amplitude_0(self, pulse_shape: SNZ):
        """Testing that the corner case amplitude = 0 works properly."""
        ENV_DURATION = 10
        envelope = pulse_shape.envelope(amplitude=0, duration=ENV_DURATION)
        assert np.allclose(envelope, np.zeros(ENV_DURATION))


class TestCornerCase:
    """Test corner case"""

    def test_snz_with_t_phi_float(self):
        """Testing that the corner case where t_phi is a float raises the warning properly."""
        with pytest.raises(
            TypeError,
            match="t_phi for pulse SNZ has to be an integer. Since min time resolution is 1ns",
        ):
            _ = SNZ(b=0.1, t_phi=1.1)
