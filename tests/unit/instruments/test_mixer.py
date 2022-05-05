import pytest

from qililab.instruments import Mixer, MixerDown, MixerUp
from qililab.typings import Category

from ..data import mixer_0_settings_sample


def mixer_up() -> MixerUp:
    """Load Mixer.

    Returns:
        Mixer: Instance of the Mixer class.
    """
    settings = mixer_0_settings_sample.copy()
    settings.pop("name")
    return MixerUp(settings=settings)


def mixer_down() -> MixerDown:
    """Load Mixer.

    Returns:
        Mixer: Instance of the Mixer class.
    """
    settings = mixer_0_settings_sample.copy()
    settings.pop("name")
    return MixerDown(settings=settings)


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
