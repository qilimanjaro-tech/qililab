""" Time Domain Readout Bus """

from dataclasses import dataclass

from qililab.instruments import TimeDomainReadoutSystemControl
from qililab.platform.components.bus import TimeDomainBus
from qililab.typings.enums import BusSubCategory


class TimeDomainReadoutBus(TimeDomainBus):
    """Time Domain Readout Bus"""

    @dataclass
    class TimeDomainReadoutBusSettings(TimeDomainBus.TimeDomainBusSettings):
        """Contains the settings of a specific time domain readout bus."""

        bus_subcategory = BusSubCategory.TIME_DOMAIN_READOUT
        system_control: TimeDomainReadoutSystemControl

    settings: TimeDomainReadoutBusSettings
