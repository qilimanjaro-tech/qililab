""" Time Domain BaseBand Bus """

from dataclasses import dataclass

from qililab.platform.components.bus_types.time_domain_bus import TimeDomainBus
from qililab.system_controls.system_control_types import BaseBandSystemControl
from qililab.typings.enums import BusName, BusSubCategory
from qililab.utils import Factory


@Factory.register
class BaseBandBus(TimeDomainBus):
    """Time Domain Base Band Bus"""

    name = BusName.TIME_DOMAIN_BASEBAND_BUS

    @dataclass
    class BaseBandBusSettings(TimeDomainBus.TimeDomainBusSettings):
        """Contains the settings of a specific time domain baseband bus."""

        bus_subcategory = BusSubCategory.BASEBAND
        system_control: BaseBandSystemControl

    settings: BaseBandBusSettings
