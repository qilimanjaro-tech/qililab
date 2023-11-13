import numpy as np
import pytest

from qililab.waveforms import IQPair, Square


@pytest.fixture(name="iq_pair")
def fixture_iq_pair() -> IQPair:
    return IQPair(I=Square(amplitude=0.5, duration=100), Q=Square(amplitude=1.0, duration=100))


class TestSquare:
    def test_init(self, iq_pair: IQPair):
        """Test __init__ method."""
        assert iq_pair.I.amplitude == 0.5
        assert iq_pair.I.duration == 100
        assert iq_pair.Q.amplitude == 1.0
        assert iq_pair.Q.duration == 100

    def test_get_duration_method(self, iq_pair: IQPair):
        """Test get_duration method."""
        assert iq_pair.get_duration() == 100

    def test_iq_pair_with_different_durations_throws_error(self):
        """Test that waveforms of an IQ pair must have the same duration."""
        with pytest.raises(ValueError, match="Waveforms of an IQ pair must have the same duration."):
            IQPair(I=Square(amplitude=0.5, duration=200), Q=Square(amplitude=1.0, duration=100))
