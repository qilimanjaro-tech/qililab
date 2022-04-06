from dataclasses import dataclass

from qililab.settings.platform import PlatformSettings
from qililab.settings.qblox_pulsar_qcm import QbloxPulsarQCMSettings
from qililab.settings.qblox_pulsar_qrm import QbloxPulsarQRMSettings
from qililab.settings.qubit import QubitCalibrationSettings
from qililab.settings.sgs100a import SGS100ASettings


@dataclass
class SettingsHashTable:
    """Hash table that maps strings to settings classes"""

    platform = PlatformSettings
    qubit = QubitCalibrationSettings
    qblox_qrm = QbloxPulsarQRMSettings
    qblox_qcm = QbloxPulsarQCMSettings
    platform = PlatformSettings
    qubit = QubitCalibrationSettings
    platform = PlatformSettings
    qubit = QubitCalibrationSettings
    rohde_schwarz = SGS100ASettings
