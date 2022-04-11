from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME

from .hashtable import SettingsHashTable
from .platform_settings import PlatformSettings
from .qubit_calibration_settings import QubitCalibrationSettings
from .schema_settings import SchemaSettings
from .settings import Settings
from .settings_manager import SettingsManager

# FIXME: Turn foldername into a variable
SETTINGS_MANAGER = SettingsManager(foldername=DEFAULT_SETTINGS_FOLDERNAME)
