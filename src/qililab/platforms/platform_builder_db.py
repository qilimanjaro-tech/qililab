from typing import Dict

from qililab.constants import DEFAULT_PLATFORM_FILENAME, DEFAULT_SCHEMA_FILENAME
from qililab.platforms.platform_builder import PlatformBuilder
from qililab.settings import SETTINGS_MANAGER, Settings
from qililab.typings import CategorySettings


class PlatformBuilderDB(PlatformBuilder):
    """Builder of platform objects."""

    def _load_platform_settings(self):
        """Load platform settings."""
        return SETTINGS_MANAGER.load(filename=DEFAULT_PLATFORM_FILENAME)

    def _load_schema_settings(self):
        """Load schema settings."""
        return SETTINGS_MANAGER.load(filename=DEFAULT_SCHEMA_FILENAME)

    def _load_bus_item_settings(self, item: Settings):
        """Load settings of the corresponding bus item.

        Args:
            item (Settings): Settings class containing the settings of the item.
        """
        return SETTINGS_MANAGER.load(filename=f"""{item.name}_{item.id_}""")

    def _load_qubit_settings(self, qubit_dict: Dict[str, int | float | str]):
        """Load qubit settings.

        Args:
            qubit_dict (Dict[str, int | float | str]): Dictionary containing either the id of the qubit or all the settings.
        """
        return SETTINGS_MANAGER.load(filename=f"""{CategorySettings.QUBIT.value}_{qubit_dict["id_"]}""")
