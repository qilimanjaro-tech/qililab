from dataclasses import dataclass, field
from pathlib import Path

import yaml

from qililab.utils import Singleton


@dataclass
class SettingsManager(metaclass=Singleton):
    """Class used to load configuration settings.

    Args:
        foldername (str): Name of the folder containing all the settings files.
        platform (str): Name of the platform.
    """

    foldername: str
    platform_name: str = field(init=False)

    def load(self, filename: str) -> dict:
        """Load yaml file with path 'qililab/settings/foldername/platform/filename.yml' and
        return an instance of the corresponding settings class.

        Args:
            filename (str): Name of the settings file without the extension.

        Returns:
            dict: Dictionary containing the settings.
        """
        path = str(Path(__file__).parent / self.foldername / self.platform_name / f"{filename}.yml")

        with open(path, "r") as file:
            settings = yaml.safe_load(stream=file)

        return settings
