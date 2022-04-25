from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME

from .settings import Settings
from .settings_manager import SettingsManager

# FIXME: Turn foldername into a variable
SETTINGS_MANAGER = SettingsManager(foldername=DEFAULT_SETTINGS_FOLDERNAME)
