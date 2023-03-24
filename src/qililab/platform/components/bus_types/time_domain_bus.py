""" Time Domain Bus """

from dataclasses import dataclass

from qililab.platform.components.bus import Bus
from qililab.system_controls.system_control_types import TimeDomainSystemControl
from qililab.typings.enums import BusCategory


class TimeDomainBus(Bus):
    """Time Domain Bus"""

    @dataclass
    class TimeDomainBusSettings(Bus.BusSettings):
        """Contains the settings of a specific time domain bus."""

        bus_category = BusCategory.TIME_DOMAIN
        system_control: TimeDomainSystemControl

    settings: TimeDomainBusSettings
