"""Qblox QCM class"""
from dataclasses import dataclass

from qpysequence.acquisitions import Acquisitions
from qpysequence.program import Loop, Register

from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.instruments.utils.instrument_factory import InstrumentFactory
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.typings.enums import InstrumentName


@InstrumentFactory.register
class QbloxQCM(QbloxModule):
    """Qblox QCM class.

    Args:
        settings (QBloxQCMSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_QCM

    @dataclass
    class QbloxQCMSettings(QbloxModule.QbloxModuleSettings):
        """Contains the settings of a specific pulsar."""

    settings: QbloxQCMSettings

    def _generate_acquisitions(self) -> Acquisitions:
        """Generate Acquisitions object, currently containing a single acquisition named "single", with num_bins = 1
        and index = 0.

        Returns:
            Acquisitions: Acquisitions object.
        """
        # FIXME: is it really necessary to generate acquisitions for a QCM??
        acquisitions = Acquisitions()
        acquisitions.add(name="single", num_bins=1, index=0)
        # FIXME: using first channel instead of the desired
        acquisitions.add(name="binning", num_bins=int(self.num_bins[0]) + 1, index=1)  # binned acquisition
        return acquisitions

    def _generate_weights(self) -> dict:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """
        return {}

    def _append_acquire_instruction(self, loop: Loop, register: Register):
        """Append an acquire instruction to the loop."""

    def acquire_result(self) -> QbloxResult:
        """Read the result from the AWG instrument

        Returns:
            QbloxResult: Acquired Qblox result
        """
        raise NotImplementedError
