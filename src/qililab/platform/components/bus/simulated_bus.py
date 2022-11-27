""" Simulated Bus """

from dataclasses import dataclass

from qililab.instruments import SimulatedSystemControl
from qililab.platform.components.bus import Bus
from qililab.typings.enums import BusCategory


class SimulatedBus(Bus):
    """Simulated Bus"""

    @dataclass
    class SimulatedBusSettings(Bus.BusSettings):
        """Contains the settings of a specific simulated bus."""

        bus_category = BusCategory.SIMULATED
        system_control: SimulatedSystemControl

    settings: SimulatedBusSettings
