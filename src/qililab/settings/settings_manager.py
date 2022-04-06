from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from qililab.settings.hashtable import SettingsHashTable
from qililab.settings.platform import PlatformSettings
from qililab.settings.qblox_pulsar import QbloxPulsarSettings
from qililab.settings.qubit import QubitCalibrationSettings
from qililab.settings.sgs100a import SGS100ASettings
from qililab.utils.singleton import Singleton

SettingsTypes = PlatformSettings | QubitCalibrationSettings | QbloxPulsarSettings | SGS100ASettings


@dataclass
class SettingsManager(metaclass=Singleton):
    """Class used to load and dump configuration settings.

    Args:
        foldername (str): Name of the folder containing all the settings files.
        platform (str): Name of the platform.
    """

    foldername: str
    platform_name: str = field(init=False)

    def load(self, filename: str) -> SettingsTypes:
        """Load yaml file with path 'qililab/settings/foldername/platform/filename.yml' and
        return an instance of the corresponding settings class.

        Args:
            filename (str): Name of the settings file without the extension.

        Returns:
            Settings: Dataclass containing the settings.
        """
        path = str(Path(__file__).parent / self.foldername / self.platform_name / f"{filename}.yml")

        with open(path, "r") as file:
            settings = yaml.safe_load(stream=file)

        category = settings.get("category")

        if not hasattr(SettingsHashTable, category):
            raise NotImplementedError(f"The class for the {category} settings is not implemented.")

        settings_class = getattr(SettingsHashTable, category)

        return settings_class(name=filename, location=path, **settings)

    def dump(self, settings: SettingsTypes):
        """Dump data from settings into its corresponding location.

        Args:
            settings (Settings): Dataclass containing the settings.
        """
        settings_dict = asdict(settings)
        if "location" in settings_dict:
            del settings_dict["location"]
        if "name" in settings_dict:
            del settings_dict["name"]
        with open(settings.location, "w") as file:
            yaml.dump(data=settings_dict, stream=file, sort_keys=False)
