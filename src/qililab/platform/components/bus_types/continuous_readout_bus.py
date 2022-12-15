""" Continuous Readout Bus """

from dataclasses import dataclass

from qililab.platform.components.bus_types.continuous_bus import ContinuousBus
from qililab.system_controls.system_control_types import ContinuousReadoutSystemControl
from qililab.typings.enums import BusName, BusSubCategory
from qililab.utils import Factory


@Factory.register
class ContinuousReadoutBus(ContinuousBus):
    """Continuous Readout Bus"""

    name = BusName.CONTINUOUS_READOUT_BUS

    @dataclass
    class ContinuousReadoutBusSettings(ContinuousBus.ContinuousBusSettings):
        """Contains the settings of a specific continuous readout bus."""

        bus_subcategory = BusSubCategory.CONTINUOUS_READOUT
        system_control: ContinuousReadoutSystemControl

    settings: ContinuousReadoutBusSettings
