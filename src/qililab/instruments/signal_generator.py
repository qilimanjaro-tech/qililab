"""SignalGenerator class."""
from qililab.instruments.instrument import Instrument
from qililab.settings import SignalGeneratorSettings


class SignalGenerator(Instrument):
    """Abstract base class defining all instruments used to generate signals."""

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
