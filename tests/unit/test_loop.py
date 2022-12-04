"""Tests for the Loop class."""
import pytest

from qililab.typings import Instrument, Parameter
from qililab.typings.loop import LoopOptions
from qililab.utils import Loop


class TestLoop:
    """Unit tests checking the Loop attributes and methods"""

    def test_init_num_and_step_raise_value_error(self):
        """Test raise error when giving num and step as arguments."""
        with pytest.raises(ValueError):
            Loop(alias=Instrument.AWG, parameter=Parameter.GAIN, options=LoopOptions)

    def test_range_raise_error_when_no_num_or_step(self):
        """Test raise error when no num or step is provided."""
        loop = Loop(alias=Instrument.AWG, parameter=Parameter.GAIN, options=LoopOptions)
        with pytest.raises(ValueError):
            print(loop.range)

    def test_num_loops_property(self, loop: Loop):
        """Test num_loops property."""
        assert loop.num_loops == 1
