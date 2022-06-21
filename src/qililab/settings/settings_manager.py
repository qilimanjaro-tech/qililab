"""SettingsManager class."""
import os
from pathlib import Path

from qililab.constants import RUNCARD
from qililab.typings import yaml
from qililab.utils import Singleton


class SettingsManager(metaclass=Singleton):
    """Class used to load configuration settings."""

    def load(self, foldername: str, platform_name: str, filename: str) -> dict:
        """Load yaml file with path 'qililab/settings/foldername/platform/filename.yml' and
        return an instance of the corresponding settings class.

        Args:
            filename (str): Name of the settings file without the extension.

        Returns:
            dict: Dictionary containing the settings.
        """
        path = os.environ.get(RUNCARD, None)
        if path is None:
            path = str(Path(__file__).parent / foldername / platform_name / filename)

        with open(file=path, mode="r", encoding="utf8") as file:
            settings = yaml.safe_load(stream=file)

        return settings
