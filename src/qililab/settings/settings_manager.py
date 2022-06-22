"""SettingsManager class."""
import os
from pathlib import Path

from qililab.constants import RUNCARDS
from qililab.typings import yaml
from qililab.utils import Singleton


class SettingsManager(metaclass=Singleton):
    """Class used to load configuration settings."""

    def load(self, foldername: str, platform_name: str) -> dict:
        """Load yaml file with path 'qililab/settings/foldername/platform/filename.yml' and
        return an instance of the corresponding settings class.

        Args:
            filename (str): Name of the settings file without the extension.

        Returns:
            dict: Dictionary containing the settings.
        """
        runcards_path = os.environ.get(RUNCARDS, None)
        if runcards_path is None:
            runcards_path = str(Path(__file__).parent / foldername)

        with open(file=f"{runcards_path}/{platform_name}.yml", mode="r", encoding="utf8") as file:
            settings = yaml.safe_load(stream=file)

        return settings
