"""Qblox pulsar QCM class"""
from dataclasses import dataclass

from qililab.instruments.qblox.qblox_pulsar import QbloxPulsar
from qililab.instruments.qubit_control import QubitControl


class QbloxPulsarQCM(QbloxPulsar, QubitControl):
    """Qblox pulsar QCM class.

    Args:
        settings (QBloxPulsarQCMSettings): Settings of the instrument.
    """

    @dataclass
    class QbloxPulsarQCMSettings(QbloxPulsar.QbloxPulsarSettings, QubitControl.QubitControlSettings):
        """Contains the settings of a specific pulsar."""

    settings: QbloxPulsarQCMSettings

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = self.QbloxPulsarQCMSettings(**settings)
