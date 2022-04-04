from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from qililab.settings.abstract_settings import AbstractSettings
from qililab.settings.hashtable import SettingsHashTable
from qililab.utils import Singleton


@dataclass
class SettingsManager(metaclass=Singleton):
    """Class used to load and dump configuration settings.

    Args:
        foldername (str): Name of the folder containing all the settings files.
        platform (str): Name of the platform.
    """

    foldername: str
    platform: str = field(init=False)

    # FIXME: Return type depends on value of category
    def load(self, filename: str, category: str) -> AbstractSettings:
        """Load yaml file with path 'qililab/settings/foldername/platform/filename.yml' and
        return an instance of a settings class specified by the 'category' argument.

        Args:
            filename (str): Name of the settings file without the extension.
            category (str): Settings category. Options are "instrument", "platform", "qubit" and "resonator".

        Returns:
            AbstractSettings: Dataclass containing the settings.
        """
        if not hasattr(SettingsHashTable, category):
            raise NotImplementedError(f"The class for the {category} settings is not implemented.")

        settings_class = getattr(SettingsHashTable, category)

        path = str(Path(__file__).parent / self.foldername / self.platform / f"{filename}.yml")

        with open(path, "r") as file:
            settings = yaml.safe_load(stream=file)

        return settings_class(name=filename, location=path, **settings)

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
