import pytest

from qililab.instruments import Mixer

from ..data import mixer_0_settings_sample


@pytest.fixture(name="mixer")
def fixture_mixer() -> Mixer:
    """Load Mixer.

    Returns:
        Mixer: Instance of the Mixer class.
    """

    return Mixer(settings=mixer_0_settings_sample)


class TestMixer:
    """Unit tests checking the Mixer attributes and methods."""

    def test_id_property(self, mixer: Mixer):
        """Test id property."""
        assert mixer.id_ == mixer.settings.id_

    def test_name_property(self, mixer: Mixer):
        """Test name property."""
        assert mixer.name == mixer.settings.name

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

    def test_up_conversion_property(self, mixer: Mixer):
        """Test up_conversion_property."""
        assert mixer.up_conversion == mixer.settings.up_conversion
