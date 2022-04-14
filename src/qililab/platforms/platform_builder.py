from qililab.buses import Bus, Buses
from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_FILENAME, DEFAULT_SCHEMA_FILENAME
from qililab.platforms.platform import Platform
from qililab.resonator import Resonator
from qililab.schema import Schema
from qililab.settings import SETTINGS_MANAGER
from qililab.typings import CategorySettings
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
        """Build platform schema"""
        schema_settings = SETTINGS_MANAGER.load(filename=DEFAULT_SCHEMA_FILENAME)
        schema = Schema(settings=schema_settings)
        self.platform.load_schema(schema=schema)

    def _build_buses(self):
        """Build platform buses"""
        buses = Buses()
        schema = self.platform.schema
        for bus in schema.settings.buses:
            bus_kwargs = {}
            for item in bus:
                settings = SETTINGS_MANAGER.load(filename=f"""{item.name}_{item.id_}""")
                if item.category == "resonator":
                    element = self._load_resonator(settings=settings)
                element = self._load_element(settings=settings)
                bus_kwargs[item.category.value] = element

            buses.append(Bus(**bus_kwargs))

        self.platform.load_buses(buses=buses)

    def _load_element(self, settings: dict):
        """Load class instance of the corresponding category.

        Args:
            settings (dict): Settings of the category object.

        Returns:
            (Platform | QbloxPulsarQRM | QbloxPulsarQCM | SGS100A | Resonator | Qubit): Class instance of the element.
        """
        element_type = NameHashTable.get(settings["name"])
        return element_type(settings)

    def _load_resonator(self, settings: dict) -> Resonator:
        """Load instance of qubits connected to the resonator, then load instance of Resonator class.

        Args:
            item (Settings): Class describing the info of the resonator to load.

        Returns:
            Resonator: Class instance of the resonator.
        """
        # Load qubits
        qubits = []
        for id_ in settings["qubits"]:
            qubit_settings = SETTINGS_MANAGER.load(filename=f"""{CategorySettings.name}_{id_}""")
            qubit = self._load_element(settings=qubit_settings)
            qubits.append(qubit)
        settings["qubits"] = qubits
        # Load resonator
        resonator: Resonator = self._load_element(settings=settings)
        return resonator
