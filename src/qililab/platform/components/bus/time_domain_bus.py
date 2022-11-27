""" Time Domain Bus """

from dataclasses import dataclass

from qililab.instruments import TimeDomainSystemControl
from qililab.platform.components.bus import Bus
from qililab.typings.enums import BusCategory


class TimeDomainBus(Bus):
    """Time Domain Bus"""

    @dataclass
    class TimeDomainBusSettings(Bus.BusSettings):
        """Contains the settings of a specific time domain bus."""

        bus_category = BusCategory.TIME_DOMAIN
        system_control: TimeDomainSystemControl

    settings: TimeDomainBusSettings

    @property
    def frequency(self):
        """TimeDomain System Control 'frequency' property."""
        return self.settings.system_control.frequency  # pylint: disable=no-member
