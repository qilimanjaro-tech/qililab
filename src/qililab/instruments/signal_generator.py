"""SignalGenerator class."""
from abc import abstractmethod
from dataclasses import dataclass, field

from qililab.constants import SIGNAL_GENERATOR
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
        frequency: float | None = field(init=False, default=None)

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

    @abstractmethod
    def turn_on(self):
        """Turn instrument on."""

    def to_dict(self):
        """Return a dict representation of the BusElement class."""
        return {key: value for key, value in super().to_dict().items() if key != SIGNAL_GENERATOR.FREQUENCY}
