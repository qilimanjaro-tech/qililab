"""Tests for the PulseShape class."""
import numpy as np
import pytest

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape import Drag, Gaussian, PulseShape, Rectangular
from qililab.typings.enums import PulseShapeSettingsName
from qililab.utils import Factory


@pytest.fixture(
    name="pulse_shape", params=[Rectangular(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, drag_coefficient=1.0)]
)
def fixture_pulse_shape(request: pytest.FixtureRequest) -> PulseShape:
    """Return Rectangular object."""
    return request.param  # type: ignore


class TestPulseShape:
    """Unit tests checking the PulseShape attributes and methods"""

    def test_envelope_method(self, pulse_shape: PulseShape):
        """Test envelope method"""
        envelope = pulse_shape.envelope(duration=50, amplitude=1.0, resolution=0.1)
        envelope2 = pulse_shape.envelope(duration=50, amplitude=1.0)
        envelope3 = pulse_shape.envelope(duration=500, amplitude=2.0)

        for env in [envelope, envelope2, envelope3]:
            assert env is not None
            assert isinstance(env, np.ndarray)

        assert round(np.max(np.abs(envelope)), 14) == 1.0
        assert round(np.max(np.abs(envelope2)), 14) == 1.0
        assert round(np.max(np.abs(envelope3)), 14) == 2.0

        assert len(envelope) == len(envelope2) * 10 == len(envelope3)

        if isinstance(pulse_shape, Rectangular):
            assert np.max(np.abs(envelope)) == np.min(np.abs(envelope))

        # if isinstance(pulse_shape, Gaussian):
        # assert np.max(np.abs(envelope)) == np.min(np.abs(envelope))

    def test_from_dict(self, pulse_shape: PulseShape):
        """Test for the to_dict method."""
        dictionary = pulse_shape.to_dict()
        pulse_shape2: PulseShape = Factory.get(name=pulse_shape.name).from_dict(dictionary)

        dictionary2 = pulse_shape2.to_dict()
        pulse_shape3: PulseShape = Factory.get(name=pulse_shape2.name).from_dict(dictionary2)

        for shape in [pulse_shape2, pulse_shape3]:
            assert shape is not None
            assert isinstance(shape, PulseShape)
            assert isinstance(shape, Factory.get(name=pulse_shape.name))

        assert pulse_shape == pulse_shape2 == pulse_shape3

    def test_to_dict_method(self, pulse_shape: PulseShape):
        """Test to_dict method"""
        dictionary = pulse_shape.to_dict()

        pulse_shape2: PulseShape = Factory.get(name=pulse_shape.name).from_dict(dictionary)
        dictionary2 = pulse_shape2.to_dict()

        for dict_ in [dictionary, dictionary2]:
            assert dict_ is not None
            assert isinstance(dict_, dict)

        if isinstance(pulse_shape, Rectangular):
            assert (
                dictionary
                == dictionary2
                == {
                    RUNCARD.NAME: pulse_shape.name.value,
                }
            )

        if isinstance(pulse_shape, Gaussian):
            assert (
                dictionary
                == dictionary2
                == {
                    RUNCARD.NAME: pulse_shape.name.value,
                    PulseShapeSettingsName.NUM_SIGMAS.value: pulse_shape.num_sigmas,
                }
            )

        if isinstance(pulse_shape, Drag):
            assert (
                dictionary
                == dictionary2
                == {
                    RUNCARD.NAME: pulse_shape.name.value,
                    PulseShapeSettingsName.NUM_SIGMAS.value: pulse_shape.num_sigmas,
                    PulseShapeSettingsName.DRAG_COEFFICIENT.value: pulse_shape.drag_coefficient,
                }
            )
