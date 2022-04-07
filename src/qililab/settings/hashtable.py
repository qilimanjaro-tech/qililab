from dataclasses import dataclass

from qililab.settings.instruments.qblox.qblox_pulsar_qcm import QbloxPulsarQCMSettings
from qililab.settings.instruments.qblox.qblox_pulsar_qrm import QbloxPulsarQRMSettings
from qililab.settings.instruments.rohde_schwarz.sgs100a import SGS100ASettings
from qililab.settings.platform import PlatformSettings
from qililab.settings.qubit import QubitCalibrationSettings


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
