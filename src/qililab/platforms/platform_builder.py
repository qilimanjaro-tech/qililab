from typing import Dict

from qililab.buses import Bus, Buses
from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_FILENAME, DEFAULT_SCHEMA_FILENAME
from qililab.platforms.platform import Platform
from qililab.platforms.utils.name_hash_table import NameHashTable
from qililab.schema import Schema
from qililab.settings import SETTINGS_MANAGER, Settings
from qililab.typings import CategorySettings
from qililab.utils import Singleton


class PlatformBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    platform: Platform

    def build(self, platform_name: str) -> Platform:
        """Build platform.

        Args:
            platform_name (str): Name of the platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info("Building platform %s", platform_name)

        SETTINGS_MANAGER.platform_name = platform_name

        self._build_platform()
        self._build_schema()
        self._build_buses()

        return self.platform

    def _build_platform(self):
        """Build platform."""
        platform_settings = self._load_platform_settings()
        self.platform = Platform(settings=platform_settings)

    def _load_platform_settings(self):
        """Load platform settings."""
        return SETTINGS_MANAGER.load(filename=DEFAULT_PLATFORM_FILENAME)

    def _build_schema(self):
        """Build platform schema."""
        schema_settings = self._load_schema_settings()
        self.platform.schema = Schema(settings=schema_settings)

    def _load_schema_settings(self):
        """Load schema settings."""
        return SETTINGS_MANAGER.load(filename=DEFAULT_SCHEMA_FILENAME)

    def _build_buses(self):
        """Build platform buses."""
        buses = Buses()
        schema = self.platform.schema
        for bus_idx, bus in enumerate(schema.settings.buses):
            bus_kwargs = {}
            for item_idx, item in enumerate(bus):
                settings = self._load_bus_item_settings(item=item, bus_idx=bus_idx, item_idx=item_idx)
                element = self._load_bus_element(settings=settings)
                bus_kwargs[item.category.value] = element

            buses.append(Bus(**bus_kwargs))

        self.platform.buses = buses

    def _load_bus_item_settings(self, item: Settings, bus_idx: int, item_idx: int):
        """Load settings of the corresponding bus item.

        Args:
            element_settings (Dict[str, int  |  float  |  str]): Dictionary describing the bus element.
        """
        return SETTINGS_MANAGER.load(filename=f"""{item.name}_{item.id_}""")

    def _load_bus_element(self, settings: dict):
        """Load class instance of the corresponding category.

        Args:
            settings (dict): Settings of the category object.

        Returns:
            (Platform | QbloxPulsarQRM | QbloxPulsarQCM | SGS100A | Resonator | Qubit): Class instance of the element.
        """
        if settings["category"] == CategorySettings.RESONATOR.value:
            settings = self._load_resonator_qubits(settings=settings)
        element_type = NameHashTable.get(settings["name"])

        return element_type(settings)

    def _load_resonator_qubits(self, settings: dict) -> dict:
        """Load instance of qubits connected to the resonator and add them in the settings dictionary.

        Args:
            settings (dict): Dictionary of the resonator settings.

        Returns:
            dict: Dictionary of the resonator settings.
        """
        qubits = []
        for qubit_dict in settings["qubits"]:
            qubit_settings = self._load_qubit_settings(qubit_dict=qubit_dict)
            qubit = self._load_bus_element(settings=qubit_settings)
            qubits.append(qubit)
        settings["qubits"] = qubits
        return settings

    def _load_qubit_settings(self, qubit_dict: Dict[str, int | float | str]):
        """Load qubit settings.

        Args:
            qubit_dict (Dict[str, int | float | str]): Dictionary containing the id of the qubit.
        """
        return SETTINGS_MANAGER.load(filename=f"""{CategorySettings.QUBIT.value}_{qubit_dict["id_"]}""")
