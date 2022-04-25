from qililab.constants import DEFAULT_SETTINGS_FOLDERNAME

from .instruments.instrument import InstrumentSettings
from .instruments.mixer import MixerSettings
from .instruments.qblox.qblox_pulsar import QbloxPulsarSettings
from .instruments.qblox.qblox_pulsar_qcm import QbloxPulsarQCMSettings
from .instruments.qblox.qblox_pulsar_qrm import QbloxPulsarQRMSettings
from .instruments.qubit_control import QubitControlSettings
from .instruments.qubit_readout import QubitReadoutSettings
from .instruments.rohde_schwarz.sgs100a import SGS100ASettings
from .instruments.signal_generator import SignalGeneratorSettings
from .platform.components.qubit import QubitCalibrationSettings
from .platform.components.resonator import ResonatorSettings
from .platform.platform import PlatformSettings
from .settings import Settings
from .settings_manager import SettingsManager

# FIXME: Turn foldername into a variable
SETTINGS_MANAGER = SettingsManager(foldername=DEFAULT_SETTINGS_FOLDERNAME)
