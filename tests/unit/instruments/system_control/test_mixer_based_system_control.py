"""Tests for the MixerBasedSystemControl class."""
from qililab.instruments import Instrument, MixerBasedSystemControl


class TestMixerBasedSystemControl:
    """Unit tests checking the MixerBasedSystemControl attributes and methods"""

    def test_iter_method(self, mixer_based_system_control: MixerBasedSystemControl):
        """Test __iter__ method."""
        for name, value in mixer_based_system_control:
            assert isinstance(name, str)
            assert isinstance(value, Instrument)

    def test_frequency_property(self, mixer_based_system_control: MixerBasedSystemControl):
        """Test frequency property."""
        assert mixer_based_system_control.awg_frequency == mixer_based_system_control.awg.frequency

    def test_signal_generator_property(self, mixer_based_system_control: MixerBasedSystemControl):
        """Test signal_generator property."""
        assert mixer_based_system_control.signal_generator == mixer_based_system_control.settings.signal_generator

    def test_awg_property(self, mixer_based_system_control: MixerBasedSystemControl):
        """Test awg property."""
        assert mixer_based_system_control.awg == mixer_based_system_control.settings.awg

    def test_name_property(self, mixer_based_system_control: MixerBasedSystemControl):
        """Test name property."""
        assert mixer_based_system_control.name == mixer_based_system_control.settings.subcategory

    def test_id_property(self, mixer_based_system_control: MixerBasedSystemControl):
        """Test id property."""
        assert mixer_based_system_control.id_ == mixer_based_system_control.settings.id_
