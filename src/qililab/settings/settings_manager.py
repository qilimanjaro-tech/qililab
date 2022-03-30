from dataclasses import asdict, dataclass
from pathlib import Path
from typing import ClassVar

import yaml

from qililab.config import logger
from qililab.settings import AbstractSettings, SettingsHashTable


@dataclass(frozen=True)
class SettingsManager:
    """Class used to load and dump configuration settings.

    Args:
        foldername (str): Name of the folder containing all the settings files.
    """

    foldername: str
    _instance: ClassVar["SettingsManager"]

    def __new__(cls, foldername: str) -> "SettingsManager":
        """Instantiate the object only once.

        Args:
            foldername (str): Name of the folder containing the settings files.

        Returns:
            SettingsManager: Unique SettingsManager instance.
        """
        if not hasattr(cls, "_instance"):
            logger.info(f"Reading settings files from {foldername} folder.")
            cls._instance = super(SettingsManager, cls).__new__(cls)
        return cls._instance

    # FIXME: Return type depends on value of category
    def load(self, filename: str, category: str) -> AbstractSettings:
        """Load yaml file with path 'qililab/settings/foldername/category/filename.yml' and
        return an instance of a settings class specified by the 'category' argument.

        Args:
            filename (str): Name of the settings file without the extension.
            category (str): Settings category. Options are "instrument", "platform", "qubit" and "resonator".

        Returns:
            AbstractSettings: Dataclass containing the settings.
        """
        if not hasattr(SettingsHashTable, category):
            raise NotImplementedError(f"The class for the {category} settings is not implemented.")

        Settings = getattr(SettingsHashTable, category)

        path = str(Path(__file__).parent / self.foldername / category / f"{filename}.yml")

        with open(path, "r") as file:
            settings = yaml.safe_load(stream=file)

        return Settings(name=filename, location=path, **settings)

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
