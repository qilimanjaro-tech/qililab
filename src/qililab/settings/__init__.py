from .hashtable import SettingsHashTable
from .platform_settings import PlatformSettings
from .qubit_calibration_settings import QubitCalibrationSettings
from .settings import Settings
from .settings_manager import SettingsManager

# FIXME: Turn foldername into a variable
SM = SettingsManager(foldername="qili")
