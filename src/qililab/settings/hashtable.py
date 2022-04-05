from dataclasses import dataclass

from qililab.settings.platform import PlatformSettings
from qililab.settings.qblox_pulsar import QbloxPulsarSettings
from qililab.settings.qblox_pulsar_qrm import QbloxPulsarQRMSettings
from qililab.settings.qubit import QubitCalibrationSettings


@dataclass
class SettingsHashTable:
    """Hash table that maps strings to settings classes"""

    platform = PlatformSettings
    qubit = QubitCalibrationSettings
    qblox_qrm = QbloxPulsarQRMSettings
    qblox_qcm = QbloxPulsarSettings
    platform = PlatformSettings
    qubit = QubitCalibrationSettings
