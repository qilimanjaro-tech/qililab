"""CurrentSource class."""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument


class CurrentSource(Instrument):
    """Abstract base class defining all instruments used to generate currents."""

    @dataclass
    class CurrentSourceSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific signal generator.

        Args:
            current (float): Current of the instrument in A.
                Value range is (-8, 8).
        """

        current: list[float]
        span: list[str]
        ramping_enabled: list[bool]
        ramp_rate: list[float]
        dacs: list[int]

    settings: CurrentSourceSettings

    @property
    def current(self):
        """CurrentSource 'current' property.

        Returns:
            float: settings.current.
        """
        return self.settings.current

    @property
    def dacs(self):
        """CurrentSource 'dacs' property.

        Returns:
            int: settings.dacs
        """
        return self.settings.dacs

    @property
    def span(self):
        """CurrentSource 'span' property.

        Returns:
            float: settings.span.
        """
        return self.settings.span

    @property
    def ramping_enabled(self):
        """CurrentSource 'ramping_enabled' property.

        Returns:
            float: settings.ramping_enabled.
        """
        return self.settings.ramping_enabled

    @property
    def ramp_rate(self):
        """CurrentSource 'ramp_rate' property.

        Returns:
            float: settings.ramp_rate.
        """
        return self.settings.ramp_rate

    def to_dict(self):
        """Return a dict representation of the CurrentSource class."""
        return dict(super().to_dict().items())
