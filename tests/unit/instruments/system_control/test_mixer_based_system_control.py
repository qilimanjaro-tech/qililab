"""Tests for the MixerBasedSystemControl class."""
from qililab.instruments import (
    Mixer,
    MixerBasedSystemControl,
    QubitInstrument,
    SignalGenerator,
)
from qililab.typings import BusElement, Category


class TestMixerBasedSystemControl:
    """Unit tests checking the MixerBasedSystemControl attributes and methods"""

    def test_get_element_method(self, mixer_based_system_control: MixerBasedSystemControl):
        """Test get_element method."""
        qubit_instrument = mixer_based_system_control.get_element(category=Category.QUBIT_INSTRUMENT, id_=0)
        signal_generator = mixer_based_system_control.get_element(category=Category.SIGNAL_GENERATOR, id_=0)
        mixer = mixer_based_system_control.get_element(category=Category.MIXER, id_=0)
        assert (
            isinstance(qubit_instrument, QubitInstrument)
            and isinstance(signal_generator, SignalGenerator)
            and isinstance(mixer, Mixer)
        )

    def test_iter_method(self, mixer_based_system_control: MixerBasedSystemControl):
        """Test __iter__ method."""
        for name, value in mixer_based_system_control:
            assert isinstance(name, str)
            assert isinstance(value, BusElement)

    def test_frequency_property(self, mixer_based_system_control: MixerBasedSystemControl):
        """Test frequency property."""
        assert mixer_based_system_control.frequency == mixer_based_system_control.qubit_instrument.frequency

    def test_signal_generator_property(self, mixer_based_system_control: MixerBasedSystemControl):
        """Test signal_generator property."""
        assert mixer_based_system_control.signal_generator == mixer_based_system_control.settings.signal_generator

    def test_mixer_up_property(self, mixer_based_system_control: MixerBasedSystemControl):
        """Test mixer_up property."""
        assert mixer_based_system_control.mixer_up == mixer_based_system_control.settings.mixer_up

    def test_mixer_down_property(self, mixer_based_system_control: MixerBasedSystemControl):
        """Test mixer_down property."""
        assert mixer_based_system_control.mixer_down == mixer_based_system_control.settings.mixer_down

    def test_qubit_instrument_property(self, mixer_based_system_control: MixerBasedSystemControl):
        """Test qubit_instrument property."""
        assert mixer_based_system_control.qubit_instrument == mixer_based_system_control.settings.qubit_instrument
