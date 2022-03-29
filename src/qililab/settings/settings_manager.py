from dataclasses import asdict
from pathlib import Path

import yaml

from qililab.settings.abstract_settings import AbstractSettings
from qililab.settings.platform_settings import PlatformSettings
from qililab.settings.qubit_calibration_settings import QubitCalibrationSettings


class SettingsManager:
    """Class used to load and dump configuration settings."""

    _instance = None

    def __new__(cls):
        """Instantiate the object only once."""
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
        return cls._instance

    def load(self, name: str, id: str) -> AbstractSettings:
        """Load yaml file with path 'qililab/settings/id/name.yml' and return an instance of a settings class specified by the 'id' argument.

        Args:
            name (str): Name of the settings file.
            id (str): Settings identification. Options are "platform", "calibration" and "instrument".

        Returns:
            AbstractSettings: Dataclass containing the settings.
        """
        path = str(Path(__file__).parent / id / f"{name}.yml")

        with open(path, "r") as file:
            settings = yaml.safe_load(stream=file)

        if id == "platform":
            return PlatformSettings(name=name, location=path, **settings)
        elif id == "calibration":
            return QubitCalibrationSettings(name=name, location=path, **settings)
        else:
            raise NotImplementedError(f"{id} settings not implemented.")

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
