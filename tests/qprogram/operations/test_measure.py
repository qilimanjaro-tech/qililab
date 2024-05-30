import pytest

from qililab import IQPair, Square
from qililab.qprogram.operations import Measure


def test_error_int_length_and_weight_defined():
    drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
    weight_wf = IQPair(I=Square(1.0, duration=200), Q=Square(0.0, duration=200))
    with pytest.raises(ValueError, match="Weights and integration length cannot be defined at the same time."):
        Measure(bus="mock_bus", waveform=drag_wf, weights=weight_wf, integration_length=100)
