"""Qblox pulsar QCM class"""
from qililab.instruments.qblox.qblox_pulsar import QbloxPulsar
from qililab.instruments.qubit_control import QubitControl
from qililab.settings import QbloxPulsarQCMSettings


class QbloxPulsarQCM(QbloxPulsar, QubitControl):
    """Qblox pulsar QCM class"""

    settings: QbloxPulsarQCMSettings

    def __init__(self, name: str, settings: dict):
        super().__init__(name=name)
        self.settings = QbloxPulsarQCMSettings(**settings)
