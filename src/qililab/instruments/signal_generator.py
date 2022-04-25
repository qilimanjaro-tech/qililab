"""SignalGenerator class."""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument


class SignalGenerator(Instrument):
    """Abstract base class defining all instruments used to generate signals."""

    @dataclass
    class SignalGeneratorSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific signal generator.

        Args:
            id (str): ID of the settings.
            name (str): Unique name of the settings.
            category (str): General name of the settings category. Options are "platform", "qubit_control",
            "qubit_readout", "signal_generator", "qubit", "resonator", "mixer" and "schema".
            ip (str): IP address of the instrument.
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
