"""Qblox QCM class"""
from dataclasses import dataclass

from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.instruments.qubit_control import QubitControl
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName


@InstrumentFactory.register
class QbloxQCM(QbloxModule, QubitControl):
    """Qblox QCM class.

    Args:
        settings (QBloxQCMSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_QCM

    @dataclass
    class QbloxQCMSettings(QbloxModule.QbloxModuleSettings, QubitControl.QubitControlSettings):
        """Contains the settings of a specific pulsar."""

    settings: QbloxQCMSettings
