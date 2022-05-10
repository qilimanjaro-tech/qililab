"""SignalGenerator class."""
from qililab.instruments.instrument import Instrument
from qililab.typings import BusElement
from qililab.utils import nested_dataclass


class SignalGenerator(Instrument):
    """Abstract base class defining all instruments used to generate signals."""

    @nested_dataclass()
    class SignalGeneratorSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific signal generator.

        Args:
            power (float): Power of the instrument. Value range is (-120, 25).
            frequency (float): Frequency of the instrument. Value range is (1e6, 20e9).
        """

        power: float
        frequency: float

    settings: SignalGeneratorSettings

    @property
    def power(self):
        """SGS100A 'power' property.

        Returns:
            float: settings.power.
        """
        return self.settings.power

    @property
    def frequency(self):
        """SGS100A 'frequency' property.

        Returns:
            float: settings.frequency.
        """
        return self.settings.frequency
