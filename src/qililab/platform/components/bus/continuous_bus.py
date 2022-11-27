""" Continuous Bus """

from dataclasses import dataclass

from qililab.instruments import ContinuousSystemControl
from qililab.platform.components.bus import Bus
from qililab.typings.enums import BusCategory


class ContinuousBus(Bus):
    """Continuous Bus"""

    @dataclass
    class ContinuousBusSettings(Bus.BusSettings):
        """Contains the settings of a specific continuous bus."""

        bus_category = BusCategory.CONTINUOUS
        system_control: ContinuousSystemControl

    settings: ContinuousBusSettings
