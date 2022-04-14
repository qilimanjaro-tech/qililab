from qililab.buses import Bus, Buses
from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_FILENAME, DEFAULT_SCHEMA_FILENAME
from qililab.platforms.platform import Platform
from qililab.schema import Schema
from qililab.settings import SETTINGS_MANAGER, Settings
from qililab.utils import Singleton
from qililab.utils.name_hash_table import NameHashTable


class PlatformBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    platform_name: str
    platform: Platform

    def build(self, platform_name: str) -> Platform:
        """Build platform.

        Args:
            name (str): Name of the platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info("Building platform %s", platform_name)

        self.platform_name = platform_name
        SETTINGS_MANAGER.platform_name = platform_name

        self._build_platform()
        self._build_schema()
        self._build_buses()

        return self.platform

    def _build_platform(self):
        """Build platform"""
        platform_settings = SETTINGS_MANAGER.load(filename=DEFAULT_PLATFORM_FILENAME)
        self.platform = Platform(settings=platform_settings)

    def _build_schema(self):
        """Build schema"""
        schema_settings = SETTINGS_MANAGER.load(filename=DEFAULT_SCHEMA_FILENAME)
        schema = Schema(settings=schema_settings)
        self.platform.load_schema(schema=schema)

    def _build_buses(self):
        """Build buses"""
        buses = Buses()
        schema = self.platform.schema
        for bus in schema.settings.buses:
            bus_kwargs = {}
            for item in bus:
                element = self._load_element(item=item)
                bus_kwargs[item.category.value] = element

            buses.append(Bus(**bus_kwargs))

        self.platform.load_buses(buses=buses)

    def _load_element(self, item: Settings):
        """Load class instance of the corresponding item.

        Args:
            item (Settings): Class describing the info of the item to load.

        Returns:
            (Platform | QbloxPulsarQRM | QbloxPulsarQCM | SGS100A | Resonator | Qubit): Class instance of the item.
        """
        filename = f"""{item.name}_{item.id}"""
        settings = SETTINGS_MANAGER.load(filename=filename)
        element = NameHashTable.get(settings["name"])
        return element(settings)
