"""Platform Manager"""
import sys
from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from qililab.config import logger
from qililab.constants import DEFAULT_PLATFORM_DUMP_FILENAME, YAML
from qililab.platform.platform import Platform
from qililab.platform.utils import PlatformSchema
from qililab.utils import SingletonABC


class PlatformManager(ABC, metaclass=SingletonABC):
    """Manager of platform objects."""

    EXPERIMENT_SETTINGS = "experiment_settings"

    def build(self, **kwargs: str | dict) -> Platform:
        """Build platform. If 'experiment_settings' kwarg is given, add/overwrite them
        in every qubit instrument of the platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        logger.info("Building platform")
        platform_schema = PlatformSchema(**self._load_platform_settings(**kwargs))
        self._overwrite_experiment_settings(platform_schema=platform_schema, **kwargs)
        self._configure_mixer_offsets(platform_schema=platform_schema)
        return Platform(platform_schema=platform_schema)

    def dump(self, platform: Platform):
        """Dump all platform information into a YAML file.

        Args:
            platform (Platform): Platform to dump.
        """
        file_path = Path(sys.argv[0]).parent / DEFAULT_PLATFORM_DUMP_FILENAME
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            yaml.safe_dump(data=platform.to_dict(), stream=file, sort_keys=False)

    @abstractmethod
    def _load_platform_settings(self, **kwargs: str | dict) -> dict:
        """Load platform and schema settings.

        Returns:
            dict: Dictionary with platform and schema settings.
        """

    def _overwrite_experiment_settings(self, platform_schema: PlatformSchema, **kwargs: str | dict):
        """If experiment settings are given, overwrite them in every qubit instrument of the platform.

        Args:
            platform_schema (PlatformSchema): Class containing the settings of the platform.

        Raises:
            ValueError: If experiment settings is not a dictionary.
        """
        if self.EXPERIMENT_SETTINGS in kwargs:
            experiment_settings = kwargs[self.EXPERIMENT_SETTINGS]
            if not isinstance(experiment_settings, dict):
                raise ValueError(f"Please provide a dictionary for the '{self.EXPERIMENT_SETTINGS}' keyword argument.")
            for bus in platform_schema.schema.elements:
                bus.qubit_instrument[YAML.REPETITION_DURATION] = experiment_settings[YAML.REPETITION_DURATION]
                bus.qubit_instrument[YAML.HARDWARE_AVERAGE] = experiment_settings[YAML.HARDWARE_AVERAGE]
                bus.qubit_instrument[YAML.SOFTWARE_AVERAGE] = experiment_settings[YAML.SOFTWARE_AVERAGE]

    def _configure_mixer_offsets(self, platform_schema: PlatformSchema):
        """Configure offsets, epsilon and delta of qubit instrument from mixer settings
        (if they are not already defined).

        Args:
            platform_schema (PlatformSchema): Class containing the settings of the platform.
        """
        # TODO: I just realized that (if I am not wrong) we just need to know the specifications of the
        # mixer used for up-conversion. If that's the case then we can delete the MixerDown class.
        for bus in platform_schema.schema.elements:
            for name, value in bus.mixer_up:
                if name not in bus.qubit_instrument:
                    bus.qubit_instrument[name] = value
