"""Tests for the PulseShape class."""
import numpy as np
import pytest

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape import SNZ, Cosine, Drag, Gaussian, PulseShape, Rectangular
from qililab.typings.enums import PulseShapeSettingsName
from qililab.utils import Factory


@pytest.mark.parametrize(
    "pulse_shape",
    [
        Rectangular(),
        Cosine(),
        Cosine(lambda_2=0.3),
        Gaussian(num_sigmas=4),
        Drag(num_sigmas=4, drag_coefficient=1.0),
        SNZ(b=0.1, t_phi=2),
    ],
)
class TestPulseShape:
    """Unit tests checking the PulseShape attributes and methods"""

    def test_envelope_method(self, pulse_shape: PulseShape):
        """Test envelope method"""
        if isinstance(pulse_shape, SNZ):
            # SNZ does not take resolution != 1
            # SNZ duration is always even + 2 + t_phi
            envelope = pulse_shape.envelope(duration=50, amplitude=1.0, resolution=1)
            envelope2 = pulse_shape.envelope(duration=40, amplitude=1.0, resolution=1)
        else:
            envelope = pulse_shape.envelope(duration=50, amplitude=1.0, resolution=0.1)
            envelope2 = pulse_shape.envelope(duration=25, amplitude=1.0, resolution=1)

        envelope3 = pulse_shape.envelope(duration=500, amplitude=2.0, resolution=1)

        # Test not None and type
        for env in [envelope, envelope2, envelope3]:
            assert env is not None
            assert isinstance(env, np.ndarray)

        # Test  the maximums of the envelopes
        if isinstance(pulse_shape, Cosine) and pulse_shape.lambda_2 > 0.0:
            # If lambda_2 > 0.0 the max amplitude is reduced
            assert round(np.max(np.real(envelope)), int(np.sqrt(10))) < 1.0
            assert round(np.max(np.real(envelope2)), int(np.sqrt(1))) < 1.0
            assert round(np.max(np.real(envelope3)), int(np.sqrt(1))) < 2.0
            # If you check the form of this shape, the maximum never gets down 70% of the Amplitude for any lambda_2
            assert round(np.max(np.real(envelope)), int(np.sqrt(10))) > 0.7 * 1.0
            assert round(np.max(np.real(envelope2)), int(np.sqrt(1))) > 0.7 * 1.0
            assert round(np.max(np.real(envelope3)), int(np.sqrt(1))) > 0.7 * 2.0
        else:
            assert round(np.max(np.real(envelope)), int(np.sqrt(10))) == 1.0
            assert round(np.max(np.real(envelope2)), int(np.sqrt(1))) == 1.0
            assert round(np.max(np.real(envelope3)), int(np.sqrt(1))) == 2.0

        # Tests lenghts
        if isinstance(pulse_shape, SNZ):
            assert len(envelope) * 10 == len(envelope2) * 12.5 == len(envelope3)
        else:
            assert len(envelope) == len(envelope2) * 20 == len(envelope3)

        # Test shapes of the graphs for each child
        if isinstance(pulse_shape, Rectangular):
            assert np.max(envelope) == np.min(envelope)

        if isinstance(pulse_shape, SNZ):
            assert np.max(envelope) == -np.min(envelope)
            assert envelope[len(envelope) // 2] == 0

        if isinstance(pulse_shape, Cosine) and pulse_shape.lambda_2 > 0.0:
            assert np.max(envelope) != envelope[len(envelope) // 2]
            assert np.min(envelope) == envelope[0]

        if isinstance(pulse_shape, Cosine) and pulse_shape.lambda_2 <= 0.0:
            assert np.max(envelope) == envelope[len(envelope) // 2]
            assert np.min(envelope) == envelope[0]

        if isinstance(pulse_shape, Gaussian):
            assert np.max(envelope) == envelope[len(envelope) // 2]
            assert np.max(envelope) / 2 < envelope[len(envelope) // 4]
            assert np.min(envelope) == envelope[0]

        if isinstance(pulse_shape, Drag):
            assert np.max(np.real(envelope)) == np.real(envelope[len(envelope) // 2])
            assert np.max(np.real(envelope)) / 2 < np.real(envelope[len(envelope) // 4])
            assert np.min(np.real(envelope)) == np.real(envelope[0])

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

        if isinstance(pulse_shape, Cosine):
            assert (
                dictionary
                == dictionary2
                == {
                    RUNCARD.NAME: pulse_shape.name.value,
                    PulseShapeSettingsName.LAMBDA_2.value: pulse_shape.lambda_2,
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
        if isinstance(pulse_shape, SNZ):
            assert (
                dictionary
                == dictionary2
                == {
                    RUNCARD.NAME: pulse_shape.name.value,
                    PulseShapeSettingsName.B.value: pulse_shape.b,
                    PulseShapeSettingsName.T_PHI.value: pulse_shape.t_phi,
                }
            )

    def test_envelope_with_amplitude_0(self, pulse_shape):
        """Testing that the corner case amplitude = 0 works properly."""
        DURATION = 10
        envelope = pulse_shape.envelope(amplitude=0, duration=DURATION)
        assert np.allclose(envelope, np.zeros(DURATION))
