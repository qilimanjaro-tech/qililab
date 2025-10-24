import numpy as np
import pytest

from qililab.waveforms import DragCorrection, Gaussian, IQPair, IQDrag, Square


@pytest.fixture(name="iq_pair")
def fixture_iq_pair() -> IQPair:
    return IQPair(I=Square(amplitude=0.5, duration=100), Q=Square(amplitude=1.0, duration=100))


class TestIQPair:
    def test_init(self, iq_pair: IQPair):
        """Test __init__ method."""
        assert getattr(iq_pair.I, "amplitude") == 0.5
        assert getattr(iq_pair.I, "duration") == 100
        assert getattr(iq_pair.Q, "amplitude") == 1.0
        assert getattr(iq_pair.Q, "duration") == 100

    def test_get_duration_method(self, iq_pair: IQPair):
        """Test get_duration method."""
        assert iq_pair.get_duration() == 100

    def test_iq_pair_with_different_durations_throws_error(self):
        """Test that waveforms of an IQ pair must have the same duration."""
        with pytest.raises(ValueError, match="Waveforms of an IQ pair must have the same duration."):
            IQPair(I=Square(amplitude=0.5, duration=200), Q=Square(amplitude=1.0, duration=100))

    def test_iq_pair_without_waveform_type_throws_error(self):
        """Test that waveforms of an IQ pair must have Waveform type."""
        with pytest.raises(TypeError, match="Waveform inside IQPair must have Waveform type."):
            IQPair(
                I=IQPair(I=Square(amplitude=0.5, duration=100), Q=Square(amplitude=1.0, duration=100)),
                Q=IQPair(I=Square(amplitude=0.5, duration=100), Q=Square(amplitude=1.0, duration=100)),
            )

    def test_drag_method(self):
        """Test __init__ method"""
        drag = IQDrag(drag_coefficient=0.4, amplitude=0.7, duration=40, num_sigmas=2)
        gaus = Gaussian(amplitude=0.7, duration=40, num_sigmas=2)
        corr = DragCorrection(drag_coefficient=0.4, waveform=gaus)

        assert isinstance(drag, IQPair)
        assert isinstance(drag.I, Gaussian)
        assert isinstance(drag.Q, DragCorrection)
        assert np.allclose(drag.I.envelope(), gaus.envelope())
        assert np.allclose(drag.Q.envelope(), corr.envelope())
