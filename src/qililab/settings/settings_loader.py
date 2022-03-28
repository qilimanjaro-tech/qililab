from pathlib import Path

import yaml

from qililab.settings.abstract_settings import AbstractSettings
from qililab.settings.platform_settings import PlatformSettings
from qililab.settings.qubit_calibration_settings import QubitCalibrationSettings


class SettingsLoader:
    """Loads settings data and creates a specific instance of a settigns dataclass."""

    def __new__(cls, id: str, name: str):
        """Returns an instance of a settings class specified by the 'id' argument.

        Args:
            id (str): Settings identification. Options are "platform", "calibration" and "instrument".
            name (str): Name of the settings file.

        Returns:
            AbstractSettings: Dataclass containing the settings.
        """
        path = str(Path(__file__).parent / id / f"{name}.yml")

        try:
            with open(path, "r") as file:
                settings = yaml.safe_load(stream=file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find settings file located in: {path}")

        if id == "platform":
            return PlatformSettings(name=name, location=path, **settings)
        elif id == "calibration":
            if name == "qubit":
                return QubitCalibrationSettings(name=name, location=path, **settings)
            else:
                raise NotImplementedError(f"{id} settings of {name} not implemented.")
        else:
            raise NotImplementedError(f"{id} settings not implemented.")
