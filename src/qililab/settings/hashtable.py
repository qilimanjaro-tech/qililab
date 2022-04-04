from dataclasses import dataclass
from typing import ClassVar, Type

from qililab.settings.platform import PlatformSettings
from qililab.settings.qubit import QubitCalibrationSettings


@dataclass
class SettingsHashTable:
    """Hash table that maps strings to settings classes"""

    platform: ClassVar[Type[PlatformSettings]] = PlatformSettings
    qubit: ClassVar[Type[QubitCalibrationSettings]] = QubitCalibrationSettings
