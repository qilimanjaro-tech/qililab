"""SignalGenerator class."""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument


class SignalGenerator(Instrument):
    """Abstract base class defining all instruments used to generate signals."""

    @dataclass
    class SignalGeneratorSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific signal generator.

        Args:
            power (float): Power of the instrument. Value range is (-120, 25).
            frequency (float): Frequency of the instrument. Value range is (1e6, 20e9).
        """

        power: float
        frequency: float
        rf_on: bool

    settings: SignalGeneratorSettings

    @property
    def power(self):
        """SignalGenerator 'power' property.

        Returns:
            float: settings.power.
        """
        return self.settings.power

    @property
    def frequency(self):
        """SignalGenerator 'frequency' property.

        Returns:
            float: settings.frequency.
        """
        return self.settings.frequency

    @property
    def rf_on(self):
        """SignalGenerator 'rf_on' property.
        Returns:
            bool: settings.rf_on.
        """
        return self.settings.rf_on

    def to_dict(self):
        """Return a dict representation of the SignalGenerator class."""
        return dict(super().to_dict().items())
