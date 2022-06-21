"""Tests for the Loop class."""
import pytest

from qililab.typings import Instrument, Parameter
from qililab.utils import Loop


class TestLoop:
    """Unit tests checking the Loop attributes and methods"""

    def test_init_num_and_step_raise_value_error(self):
        """Test raise error when giving num and step as arguments."""
        with pytest.raises(ValueError):
            Loop(instrument=Instrument.AWG, id_=0, parameter=Parameter.GAIN, start=0, stop=1, num=10, step=0.1)

    def test_range_raise_error_when_no_num_or_step(self):
        """Test raise error when no num or step is provided."""
        loop = Loop(instrument=Instrument.AWG, id_=0, parameter=Parameter.GAIN, start=0, stop=1)
        with pytest.raises(ValueError):
            print(loop.range)

    def test_num_loops_property(self, loop: Loop):
        """Test num_loops property."""
        assert loop.num_loops == 1
