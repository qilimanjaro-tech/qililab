""" Simulated Bus """


from copy import deepcopy
from dataclasses import dataclass

from qililab.constants import RUNCARD
from qililab.instruments.instruments import Instruments
from qililab.platform.components.bus import Bus
from qililab.system_controls.system_control_types import SimulatedSystemControl
from qililab.typings.enums import BusCategory, BusName, BusSubCategory, Category
from qililab.utils.factory import Factory


@Factory.register
class SimulatedBus(Bus):
    """Simulated Bus"""

    name = BusName.SIMULATED_BUS

    @dataclass
    class SimulatedBusSettings(Bus.BusSettings):
        """Contains the settings of a specific simulated bus."""

        bus_category = BusCategory.SIMULATED
        bus_subcategory = BusSubCategory.SIMULATED
        system_control: SimulatedSystemControl

    settings: SimulatedBusSettings

    def _replace_settings_dicts_with_instrument_objects(self, instruments: Instruments):
        """Replace dictionaries from settings into its respective instrument classes."""
        for name, value in deepcopy(self.settings):
            system_control = None
            category = Category(name)
            if category == Category.SYSTEM_CONTROL and isinstance(value, dict):
                system_control_category = value.get(RUNCARD.SYSTEM_CONTROL_CATEGORY)
                if not isinstance(system_control_category, str):
                    raise ValueError(f"Invalid value for system_control_category: {system_control_category}")
                system_control_subcategory = value.get(RUNCARD.SYSTEM_CONTROL_SUBCATEGORY)
                if system_control_subcategory is not None and not isinstance(system_control_category, str):
                    raise ValueError(f"Invalid value for system_control_subcategory: {system_control_subcategory}")
                system_control = Factory.get(name=value.pop(RUNCARD.NAME))(settings=value)
            if system_control is None:
                raise ValueError(f"No system_control found for category {category.value} and value {value}.")
            setattr(self.settings, name, system_control)

    @property
    def frequency(self):
        """Simulated 'frequency' property."""
        if self.target_freqs[0] is None:
            raise ValueError("No target frequency found")
        return float(self.target_freqs[0])  # FIXME: adapt to the correct target frequency
