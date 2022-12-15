""" Time Domain Control Bus """

from dataclasses import dataclass

from qililab.platform.components.bus_types.time_domain_bus import TimeDomainBus
from qililab.system_controls.system_control_types import ControlSystemControl
from qililab.typings.enums import BusName, BusSubCategory
from qililab.utils import Factory


@Factory.register
class ControlBus(TimeDomainBus):
    """Time Domain Control Bus"""

    name = BusName.TIME_DOMAIN_CONTROL_BUS

    @dataclass
    class ControlBusSettings(TimeDomainBus.TimeDomainBusSettings):
        """Contains the settings of a specific time domain control bus."""

        bus_subcategory = BusSubCategory.CONTROL
        system_control: ControlSystemControl

    settings: ControlBusSettings
