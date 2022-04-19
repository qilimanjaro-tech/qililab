import yaml

from qililab.buses import Bus, Buses
from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_FILENAME, DEFAULT_SCHEMA_FILENAME
from qililab.platforms.platform import Platform
from qililab.platforms.utils.name_hash_table import NameHashTable
from qililab.schema import Schema
from qililab.settings import SETTINGS_MANAGER
from qililab.typings import CategorySettings
from qililab.utils import Singleton


class PlatformBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    platform: Platform
    yaml_data: dict
    _load_from_yaml: bool = False

    def build(self, platform_name: str, filepath: str | None = None) -> Platform:
        """Build platform.

        Args:
            platform_name (str): Name of the platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info("Building platform %s", platform_name)

        if filepath is None:
            SETTINGS_MANAGER.platform_name = platform_name
        else:
            self._load_from_yaml = True
            with open(file=filepath, mode="r", encoding="utf-8") as file:
                self.yaml_data = yaml.safe_load(file)

        self._build_platform()
        self._build_schema()
        self._build_buses()

        return self.platform

    def _build_platform(self):
        """Build platform"""
        if self._load_from_yaml:
            platform_settings = self.yaml_data[CategorySettings.PLATFORM.value]
        else:
            platform_settings = SETTINGS_MANAGER.load(filename=DEFAULT_PLATFORM_FILENAME)
        self.platform = Platform(settings=platform_settings)

    def _build_schema(self):
        """Build platform schema"""
        if self._load_from_yaml:
            schema_settings = self.yaml_data[CategorySettings.SCHEMA.value]
        else:
            schema_settings = SETTINGS_MANAGER.load(filename=DEFAULT_SCHEMA_FILENAME)
        self.platform.schema = Schema(settings=schema_settings)

    def _build_buses(self):
        """Build platform buses"""
        buses = Buses()
        schema = self.platform.schema
        for bus_idx, bus in enumerate(schema.settings.buses):
            bus_kwargs = {}
            for item_idx, item in enumerate(bus):
                if self._load_from_yaml:
                    settings = self.yaml_data[CategorySettings.BUSES.value][bus_idx][item_idx]
                else:
                    settings = SETTINGS_MANAGER.load(filename=f"""{item.name}_{item.id_}""")
                element = self._load_element(settings=settings)
                bus_kwargs[item.category.value] = element

            buses.append(Bus(**bus_kwargs))

        self.platform.buses = buses

    def _load_element(self, settings: dict):
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
        for id_ in settings["qubits"]:
            if self._load_from_yaml:
                qubit_settings = id_
            else:
                qubit_settings = SETTINGS_MANAGER.load(filename=f"""{CategorySettings.QUBIT.value}_{id_}""")
            qubit = self._load_element(settings=qubit_settings)
            qubits.append(qubit)
        settings["qubits"] = qubits
        return settings
