from abc import ABC
from pathlib import Path

import yaml

from qililab.config import raise_error
from qililab.settings.settings import Settings


class SettingsLoader(ABC):
    """Class used to load a yaml file into a Settings object."""

    def __new__(cls, name: str, id: str) -> Settings:
        """Load yaml file located at "qililab/settings/id/name" and return dataclass object containing the file values.

        Args:
            name (str): Name of the settings file.
            id (str): Settings identification. Options are "platform", "calibration", "instrument", "qubit" and "cavity".

        Returns:
            Settings: Dataclass containing the yaml settings.
        """
        path = Path(__file__).parent / id / name

        with open(path, "r") as file:
            settings = yaml.safe_load(stream=file)

        return Settings(settings=settings)
