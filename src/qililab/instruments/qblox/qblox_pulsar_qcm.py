"""Qblox pulsar QCM class"""
from dataclasses import dataclass

from qililab.instruments.qblox.qblox_pulsar import QbloxPulsar
from qililab.instruments.qubit_control import QubitControl
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName


@InstrumentFactory.register
class QbloxPulsarQCM(QbloxPulsar, QubitControl):
    """Qblox pulsar QCM class.

    Args:
        settings (QBloxPulsarQCMSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_QCM

    @dataclass
    class QbloxPulsarQCMSettings(QbloxPulsar.QbloxPulsarSettings, QubitControl.QubitControlSettings):
        """Contains the settings of a specific pulsar."""

    settings: QbloxPulsarQCMSettings
