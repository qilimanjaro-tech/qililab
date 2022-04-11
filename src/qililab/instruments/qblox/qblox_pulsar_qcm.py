"""Qblox pulsar QCM class"""
from qililab.instruments.qblox.qblox_pulsar import QbloxPulsar
from qililab.instruments.qubit_control import QubitControl


class QbloxPulsarQCM(QbloxPulsar, QubitControl):
    """Qblox pulsar QCM class"""
