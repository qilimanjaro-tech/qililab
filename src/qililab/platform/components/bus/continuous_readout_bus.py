""" Continuous Readout Bus """

from dataclasses import dataclass

from qililab.instruments import ContinuousReadoutSystemControl
from qililab.platform.components.bus import ContinuousBus
from qililab.typings.enums import BusSubCategory


class ContinuousReadoutBus(ContinuousBus):
    """Continuous Readout Bus"""

    @dataclass
    class ContinuousReadoutBusSettings(ContinuousBus.ContinuousBusSettings):
        """Contains the settings of a specific continuous readout bus."""

        bus_subcategory = BusSubCategory.CONTINUOUS_READOUT
        system_control: ContinuousReadoutSystemControl

    settings: ContinuousReadoutBusSettings
