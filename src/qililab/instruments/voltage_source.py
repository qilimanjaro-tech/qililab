"""VoltageSource class."""

from dataclasses import dataclass

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

        voltage: list[float]
        span: list[str]
        ramping_enabled: list[bool]
        ramp_rate: list[float]
        dacs: list[int]  # indices of the dacs to use

    settings: VoltageSourceSettings

    @property
    def voltage(self):
        """VoltageSource 'voltage' property.

        Returns:
            float: settings.voltage.
        """
        return self.settings.voltage

    @property
    def dacs(self):
        """CurrentSource 'dacs' property.

        Returns:
            int: settings.dacs
        """
        return self.settings.dacs

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

    def to_dict(self):
        """Return a dict representation of the VoltageSource class."""
        return dict(super().to_dict().items())
