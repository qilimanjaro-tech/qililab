""" Time Domain Control Bus """

from dataclasses import dataclass

from qililab.instruments import ControlSystemControl
from qililab.platform.components.bus import TimeDomainBus
from qililab.typings.enums import BusSubCategory


class ControlBus(TimeDomainBus):
    """Time Domain Control Bus"""

    @dataclass
    class ControlBusSettings(TimeDomainBus.TimeDomainBusSettings):
        """Contains the settings of a specific time domain control bus."""

        bus_subcategory = BusSubCategory.CONTROL
        system_control: ControlSystemControl

    settings: ControlBusSettings
