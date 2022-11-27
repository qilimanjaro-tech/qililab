""" Simulated Bus """

from dataclasses import dataclass

from qililab.platform.components.bus import Bus
from qililab.system_controls.system_control_types import SimulatedSystemControl
from qililab.typings.enums import BusCategory, BusName
from qililab.utils.factory import Factory


@Factory.register
class SimulatedBus(Bus):
    """Simulated Bus"""

    name = BusName.SIMULATED_BUS

    @dataclass
    class SimulatedBusSettings(Bus.BusSettings):
        """Contains the settings of a specific simulated bus."""

        bus_category = BusCategory.SIMULATED
        system_control: SimulatedSystemControl

    settings: SimulatedBusSettings
