from .abstract_settings import AbstractSettings
from .platform_settings import PlatformSettings
from .qubit_calibration_settings import QubitCalibrationSettings
from .settings_manager import SettingsManager

# FIXME: Turn foldername into a variable
SM = SettingsManager(foldername="qili")
