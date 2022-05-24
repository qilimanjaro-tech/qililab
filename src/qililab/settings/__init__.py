"""__init__.py"""
from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME

from .settings import Settings
from .settings_manager import SettingsManager

SETTINGS_MANAGER = SettingsManager()
