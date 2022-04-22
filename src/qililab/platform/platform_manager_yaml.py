from typing import Dict, List

import numpy as np
import yaml

from qililab.platform.platform import Platform
from qililab.platform.platform_manager import PlatformManager
from qililab.settings import Settings
from qililab.typings import CategorySettings


class PlatformManagerYAML(PlatformManager):
    """Manager of platform objects. Uses YAML file to get the corresponding settings."""

    all_platform: Dict
    yaml_buses: List[List[Settings]]

    def build(self, platform_name: str) -> Platform:
        """Build platform.

        Args:
            platform_name (str): Name of the platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        if not hasattr(self, "all_platform"):
            raise AttributeError("Please use the 'build_from_yaml' method.")

        return super().build(platform_name=platform_name)

    def build_from_yaml(self, filepath: str) -> Platform:
        """Build platform from YAML file.

        Args:
            filepath (str): Path to the YAML file.

        Returns:
            Platform: Platform object describing the setup used.
        """
        self._load_yaml_data(filepath=filepath)
        return self.build(platform_name=self.all_platform["platform"]["name"])

    def _load_yaml_data(self, filepath: str):
        """Load YAML file and save it to all_platform attribute.

        Args:
            filepath (str): Path to the YAML file.
        """
        with open(file=filepath, mode="r", encoding="utf-8") as file:
            self.all_platform = yaml.safe_load(file)

        self._load_yaml_buses_data()

    def _load_yaml_buses_data(self):
        """Get id_, name and category of each item inside buses, cast it to Settings and save it
        into the yaml_buses attribute. This will be later be used by the _load_bus_item_settings method."""
        self.yaml_buses = np.array(
            [
                [Settings(id_=item["id_"], name=item["name"], category=item["category"]) for item in bus]
                for bus in self.all_platform[CategorySettings.BUSES.value]
            ]
        )

    def _load_platform_settings(self):
        """Load platform settings."""
        return self.all_platform[CategorySettings.PLATFORM.value]

    def _load_schema_settings(self):
        """Load schema settings."""
        return self.all_platform[CategorySettings.SCHEMA.value]

    def _load_bus_item_settings(self, item: Settings) -> Dict[str, int | float | str]:
        """Searches for 'item' in 'yaml_buses' and loads its complete settings.

        Args:
            item (Settings): Settings class containing the id, name and category of the item.

        Raises:
            ValueError: If there is

        Returns:
            Dict[str, int | float | str]: _description_
        """
        mask = self.yaml_buses == item
        if np.sum(mask) == 0:
            raise ValueError(f"Item with name {item.name} and id {item.id_} was not found in buses.")
        settings = np.array(self.all_platform[CategorySettings.BUSES.value])[mask][0]
        return settings

    def _load_qubit_settings(self, qubit_dict: Dict[str, int | float | str]):
        """Load qubit settings.

        Args:
            qubit_dict (Dict[str, int | float | str]): Dictionary containing either the id of the qubit or all the settings.
        """
        return qubit_dict
