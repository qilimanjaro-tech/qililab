from dataclasses import asdict

import yaml

from qililab.settings.abstract_settings import AbstractSettings
from qililab.settings.settings_loader import SettingsLoader


class SettingsManager:
    """Class used to load and dump configuration settings."""

    _instance = None

    def __new__(cls):
        """Instantiate the object only once."""
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
        return cls._instance

    def load(self, name: str, id: str):
        """Load yaml file with path 'qililab/settings/id/name.yml' and return dataclass object containing the file values.

        Args:
            name (str): Name of the settings file.
            id (str): Settings identification. Options are "platform", "calibration", "instrument", "qubit" and "cavity".

        Returns:
            AbstractSettings: Dataclass containing the settings.
        """

        return SettingsLoader(id=id, name=name)

    def dump(self, settings: AbstractSettings) -> None:
        """Dump data from settings into its corresponding location.

        Args:
            settings (AbstractSettings): Dataclass containing the settings.
        """
        settings_dict = asdict(settings)
        del settings_dict["location"]
        del settings_dict["name"]
        with open(settings.location, "w") as file:
            yaml.dump(data=settings_dict, stream=file)
