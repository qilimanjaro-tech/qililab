from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from qililab.settings.hashtable import SettingsHashTable
from qililab.settings.settings import Settings
from qililab.utils import Singleton


@dataclass
class SettingsManager(metaclass=Singleton):
    """Class used to load and dump configuration settings.

    Args:
        foldername (str): Name of the folder containing all the settings files.
        platform (str): Name of the platform.
    """

    foldername: str
    platform_name: str = field(init=False)

    # FIXME: Return type depends on value of category
    def load(self, filename: str) -> Settings:
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

    def dump(self, settings: Settings) -> None:
        """Dump data from settings into its corresponding location.

        Args:
            settings (Settings): Dataclass containing the settings.
        """
        settings_dict = asdict(settings)
        del settings_dict["location"]
        del settings_dict["name"]
        with open(settings.location, "w") as file:
            yaml.dump(data=settings_dict, stream=file, sort_keys=False)
