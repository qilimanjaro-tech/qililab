from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME

from .generic_qubit_instrument_settings import GenericQubitInstrumentSettings
from .settings import Settings
from .settings_manager import SettingsManager

# FIXME: Turn foldername into a variable
SETTINGS_MANAGER = SettingsManager()
