""" Time Domain BaseBand Bus """

from dataclasses import dataclass

from qililab.instruments import BaseBandSystemControl
from qililab.platform.components.bus import TimeDomainBus
from qililab.typings.enums import BusSubCategory


class BaseBandBus(TimeDomainBus):
    """Time Domain Base Band Bus"""

    @dataclass
    class BaseBandBusSettings(TimeDomainBus.TimeDomainBusSettings):
        """Contains the settings of a specific time domain baseband bus."""

        bus_subcategory = BusSubCategory.BASEBAND
        system_control: BaseBandSystemControl

    settings: BaseBandBusSettings
