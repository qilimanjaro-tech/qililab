from abc import ABC
from pathlib import Path
from typing import Union

import yaml

from qililab.settings.settings import Settings


class SettingsManager(ABC):
    """Class used to load a yaml file into a Settings object.

    Attributes:
        name (str): Name of the settings file.
        id (str): Settings identification. Options are "platform", "calibration", "instrument", "qubit" and "cavity".
        settings (Settings): Dataclass containing the settings from the specified yaml file.
    """

    def __init__(self, name: str, id: str) -> None:
        """Build path to yaml file from id and name: 'qililab/settings/id/name'

        Args:
            name (str): Name of the settings file.
            id (str): Settings identification. Options are "platform", "calibration", "instrument", "qubit" and "cavity".
        """
        # TODO: Connect to DB when available
        self.name = name
        self.id = id
        self.settings = self.load()

    def load(self) -> Settings:
        """Load yaml file located at self._path and return dataclass object containing the file values.

        Returns:
            Settings: Dataclass containing the yaml settings.
        """
        with open(self._path, "r") as file:
            settings = yaml.safe_load(stream=file)

        return Settings(settings=settings)

    def dump(self) -> None:
        """Dump dictionary from dataclass self.settings to yaml file located at self._path."""
        with open(self._path, "w") as file:
            yaml.dump(data=self.settings.asdict(), stream=file)

    @property
    def _path(self) -> Path:
        """Create and return path to yaml file from given name and id.

        Returns:
            str: Path to the yaml file.
        """
        return Path(__file__).parent / self.id / f"{self.name}.yml"

    def __getattr__(self, name: str) -> Union[str, int, float]:
        """Redirect all non-defined attribute and method calls to the class instance saved in self.settings.

        Args:
            name (str): Attribute or method to call.

        Returns:
            Union[str, int, float]: Value of the attribute or return value of the method.
        """
        return getattr(self.settings, name)
