import copy
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict

import yaml

from qililab.config import logger
from qililab.platforms.components.buses import Bus, Buses
from qililab.platforms.components.schema import Schema
from qililab.platforms.platform import Platform
from qililab.platforms.utils.bus_element_hash_table import BusElementHashTable
from qililab.settings import SETTINGS_MANAGER, Settings
from qililab.typings import CategorySettings


class PlatformManager(ABC):
    """Manager of platform objects."""

    def build(self, platform_name: str) -> Platform:
        """Build platform.

        Args:
            platform_name (str): Name of the platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info("Building platform %s", platform_name)

        SETTINGS_MANAGER.platform_name = platform_name

        schema = self._build_schema()
        buses = self._build_buses(schema=schema)
        return self._build_platform(schema=schema, buses=buses)

    def dump(self, platform: Platform):
        """Dump all platform information into a YAML file.

        Args:
            platform (Platform): Platform to dump.
        """
        file_path = Path(sys.argv[0]).parent / "platform.yml"
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            yaml.safe_dump(data=platform.to_dict(), stream=file, sort_keys=False)

    def _build_platform(self, schema: Schema, buses: Buses) -> Platform:
        """Build platform."""
        platform_settings = self._load_platform_settings()
        return Platform(settings=platform_settings, schema=schema, buses=buses)

    def _build_schema(self) -> Schema:
        """Build platform schema."""
        schema_settings = self._load_schema_settings()
        return Schema(settings=schema_settings)

    def _build_buses(self, schema) -> Buses:
        """Build platform buses."""
        buses = Buses()
        for bus in schema.settings.buses:
            bus_kwargs = {}
            for item in bus:
                settings = self._load_bus_item_settings(item=item)
                element = self._load_bus_element(settings=settings)
                bus_kwargs[item.category.value] = element

            buses.append(Bus(**bus_kwargs))

        return buses

    def _load_bus_element(self, settings: dict):
        """Load class instance of the corresponding category.

        Args:
            settings (dict): Settings of the category object.

        Returns:
            (Platform | QbloxPulsarQRM | QbloxPulsarQCM | SGS100A | Resonator | Qubit): Class instance of the element.
        """
        if CategorySettings(settings["category"]) == CategorySettings.RESONATOR:
            settings = self._load_resonator_qubits(settings=settings)
        element_type = BusElementHashTable.get(settings["name"])

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
        settings_copy = copy.deepcopy(settings)
        settings_copy["qubits"] = qubits
        return settings_copy

    @abstractmethod
    def _load_platform_settings(self):
        """Load platform settings."""

    @abstractmethod
    def _load_schema_settings(self):
        """Load schema settings."""

    @abstractmethod
    def _load_bus_item_settings(self, item: Settings):
        """Load settings of the corresponding bus item.

        Args:
            item (Settings): Settings class containing the settings of the item.
        """

    @abstractmethod
    def _load_qubit_settings(self, qubit_dict: Dict[str, int | float | str]):
        """Load qubit settings.

        Args:
            qubit_dict (Dict[str, int | float | str]): Dictionary containing either the id of the qubit or all the settings.
        """
