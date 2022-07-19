"""VoltageSource class."""
from abc import abstractmethod
from dataclasses import dataclass

from qililab.constants import VOLTAGESOURCE
from qililab.instruments.instrument import Instrument


class VoltageSource(Instrument):
    """Abstract base class defining all instruments used to generate voltages."""

    @dataclass
    class VoltageSourceSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific signal generator.

        Args:
            voltage (float): Voltage of the instrument in V.
                Value range is (-40, 40).
        """

        voltage: float

    settings: VoltageSourceSettings

    @property
    def voltage(self):
        """VoltageSource 'voltage' property.

        Returns:
            float: settings.voltage.
        """
        return self.settings.voltage

    @abstractmethod
    def start(self):
        """Turn instrument on."""

    def to_dict(self):
        """Return a dict representation of the VoltageSource class."""
        return {key: value for key, value in super().to_dict().items() if key != VOLTAGESOURCE.VOLTAGE}
        # TODO: Ask why except VOLTAGE? (was frequency in signal generator)
