""" Time Domain Readout Bus """

from dataclasses import dataclass

from qililab.platform.components.bus_types.time_domain_bus import TimeDomainBus
from qililab.system_controls.system_control_types import TimeDomainReadoutSystemControl
from qililab.typings.enums import BusName, BusSubCategory
from qililab.utils import Factory


@Factory.register
class TimeDomainReadoutBus(TimeDomainBus):
    """Time Domain Readout Bus"""

    name = BusName.TIME_DOMAIN_READOUT_BUS

    @dataclass
    class TimeDomainReadoutBusSettings(TimeDomainBus.TimeDomainBusSettings):
        """Contains the settings of a specific time domain readout bus."""

        bus_subcategory = BusSubCategory.TIME_DOMAIN_READOUT
        system_control: TimeDomainReadoutSystemControl

    settings: TimeDomainReadoutBusSettings
