"""Tests for the Mixer class."""
import pytest

from qililab.instruments import Mixer

from ...conftest import mixer_down, mixer_up


@pytest.mark.parametrize("mixer", [mixer_up(), mixer_down()])
class TestMixer:
    """Unit tests checking the Mixer attributes and methods."""

    def test_id_property(self, mixer: Mixer):
        """Test id property."""
        assert mixer.id_ == mixer.settings.id_

    def test_category_property(self, mixer: Mixer):
        """Test category property."""
        assert mixer.category == mixer.settings.category

    def test_epsilon_property(self, mixer: Mixer):
        """Test epsilon property."""
        assert mixer.epsilon == mixer.settings.epsilon

    def test_delta_property(self, mixer: Mixer):
        """Test delta property."""
        assert mixer.delta == mixer.settings.delta

    def test_offset_i_property(self, mixer: Mixer):
        """Test offset_i property."""
        assert mixer.offset_i == mixer.settings.offset_i

    def test_offset_q_property(self, mixer: Mixer):
        """Test offset_q property."""
        assert mixer.offset_q == mixer.settings.offset_q
