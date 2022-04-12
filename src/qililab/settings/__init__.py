from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME

from .instruments.qblox.qblox_pulsar_qcm import QbloxPulsarQCMSettings
from .instruments.qblox.qblox_pulsar_qrm import QbloxPulsarQRMSettings
from .instruments.qubit_control import QubitControlSettings
from .instruments.rohde_schwarz.sgs100a import SGS100ASettings
from .settings import Settings
from .settings_manager import SettingsManager

# FIXME: Turn foldername into a variable
SETTINGS_MANAGER = SettingsManager(foldername=DEFAULT_SETTINGS_FOLDERNAME)
