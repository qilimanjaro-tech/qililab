from dataclasses import asdict, dataclass
from pathlib import Path
from typing import ClassVar, Type

import yaml

from qililab.settings.abstract_settings import AbstractSettings
from qililab.settings.platform_settings import PlatformSettings
from qililab.settings.qubit_calibration_settings import QubitCalibrationSettings


@dataclass(frozen=True)
class SettingsManager:
    """Class used to load and dump configuration settings.

    Args:
        foldername (str): Name of the folder containing all the settings files.
    """

    foldername: str
    _instance: ClassVar["SettingsManager"]

    def __new__(cls, foldername: str):
        """Instantiate the object only once."""
        if not hasattr(cls, "_instance"):
            cls._instance = super(SettingsManager, cls).__new__(cls)
        return cls._instance

    def load(self, filename: str, category: str, subfolder: str = "") -> AbstractSettings:
        """Load yaml file with path 'qililab/settings/foldername/category/subfolder/filename.yml' and
        return an instance of a settings class specified by the 'id' argument.

        Args:
            filename (str): Name of the settings file without the extension.
            category (str): Settings category. Options are "calibration", "instrument" and "platform".
            subfolder (str, optional): Name of subfolder where the settings file is located.
            Defaults to empty string.

        Returns:
            AbstractSettings: Dataclass containing the settings.
        """
        path = str(Path(__file__).parent / self.foldername / category / subfolder / f"{filename}.yml")  # path to folder

        with open(path, "r") as file:
            settings = yaml.safe_load(stream=file)

        if category == "platform":
            return PlatformSettings(name=filename, location=path, **settings)
        elif category == "calibration":
            return QubitCalibrationSettings(name=filename, location=path, **settings)
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
            yaml.dump(data=settings_dict, stream=file, sort_keys=False)
