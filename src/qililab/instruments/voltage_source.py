"""VoltageSource class."""
import string
from abc import abstractmethod
from dataclasses import dataclass
from typing import List

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
        span: str
        ramping_enabled: bool
        ramp_rate: float
        # TODO: Here a list of integers with available dacs

    settings: VoltageSourceSettings

    @property
    def voltage(self):
        """VoltageSource 'voltage' property.

        Returns:
            float: settings.voltage.
        """
        return self.settings.voltage

    @property
    def span(self):
        """VoltageSource 'span' property.

        Returns:
            float: settings.span.
        """
        return self.settings.span

    @property
    def ramping_enabled(self):
        """VoltageSource 'ramping_enabled' property.

        Returns:
            float: settings.ramping_enabled.
        """
        return self.settings.ramping_enabled

    @property
    def ramp_rate(self):
        """VoltageSource 'ramp_rate' property.

        Returns:
            float: settings.ramp_rate.
        """
        return self.settings.ramp_rate

    @abstractmethod
    def start(self):
        """Turn instrument on."""

    def to_dict(self):
        """Return a dict representation of the VoltageSource class."""
        return {key: value for key, value in super().to_dict().items() if key != VOLTAGESOURCE.VOLTAGE}
        # TODO: Ask why except VOLTAGE? (was frequency in signal generator)
