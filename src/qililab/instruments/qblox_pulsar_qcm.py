"""Qblox pulsar QCM class"""
from pulsar_qcm.pulsar_qcm import pulsar_qcm

from qililab.instruments.qblox_pulsar import QbloxPulsar


class QbloxPulsarQCM(QbloxPulsar):
    """Pulsar QCM class"""

    def __init__(self, name: str):
        super().__init__(name=name)

    def connect(self):
        """Establish connection with the instrument. Initialize self.device variable."""
        if not self._connected:
            self.device = pulsar_qcm(self.settings.name, self.settings.ip)
            self._connected = True
