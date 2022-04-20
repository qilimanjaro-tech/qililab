from typing import Dict

import yaml

from qililab.platforms.platform import Platform
from qililab.platforms.platform_builder import PlatformBuilder
from qililab.settings import Settings
from qililab.typings import CategorySettings


class PlatformBuilderYAML(PlatformBuilder):
    """Builder of platform objects. Uses YAML file to get the corresponding settings."""

    platform: Platform
    yaml_data: dict

    def build_from_yaml(self, filepath: str):
        """Build platform from YAML file.

        Args:
            filepath (str): Path to the YAML file.
        """
        with open(file=filepath, mode="r", encoding="utf-8") as file:
            self.yaml_data = yaml.safe_load(file)

        self.build(platform_name=self.yaml_data["platform"]["name"])

    def _load_platform_settings(self):
        """Load platform settings."""
        return self.yaml_data[CategorySettings.PLATFORM.value]

    def _load_schema_settings(self):
        """Load schema settings."""
        return self.yaml_data[CategorySettings.SCHEMA.value]

    def _load_bus_item_settings(self, item: Settings, bus_idx: int, item_idx: int):
        """Load settings of the corresponding bus item.

        Args:
            element_settings (Dict[str, int  |  float  |  str]): Dictionary describing the bus element.
        """
        return self.yaml_data[CategorySettings.BUSES.value][bus_idx][item_idx]

    def _load_qubit_settings(self, qubit_dict: Dict[str, int | float | str]):
        """Load qubit settings.

        Args:
            qubit_settings (Dict[str, int | float | str]): Dictionary containing the settings of the qubit.
        """
        return qubit_dict
