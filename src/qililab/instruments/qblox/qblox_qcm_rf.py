"""This file contains the QbloxQCMRF class."""
from qpysequence.program import Loop, Register
from qpysequence.weights import Weights

from qililab.instruments import Instrument
from qililab.instruments.awg_settings import AWGQbloxSequencer
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.typings import InstrumentName, Parameter

from .qblox_module import QbloxModule


class QbloxQCMRF(QbloxModule):
    """Qblox QCM-RF driver."""

    name = InstrumentName.QBLOX_QCMRF

    class QbloxQCMRFSettings(QbloxModule.QbloxModuleSettings):
        """Contains the settings of a specific Qblox QCM-RF module."""

        out0_lo_freq: float
        out0_lo_en: bool
        out0_att: float
        out0_offset_path0: float
        out0_offset_path1: float
        out1_lo_freq: float
        out1_lo_en: bool
        out1_att: float
        out1_offset_path0: float
        out1_offset_path1: float

    settings: QbloxQCMRFSettings

    def _generate_weights(self, sequencer: AWGQbloxSequencer) -> Weights:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """
        return Weights()

    def _append_acquire_instruction(self, loop: Loop, bin_index: Register | int, sequencer_id: int):
        """Append an acquire instruction to the loop."""

    def acquire_result(self) -> QbloxResult:
        """Read the result from the AWG instrument

        Returns:
            QbloxResult: Acquired Qblox result
        """
        raise NotImplementedError

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set a parameter of the Qblox QCM-RF module.

        Args:
            parameter (Parameter): Parameter name.
            value (float | str | bool): Value to set.
            channel_id (int | None, optional): ID of the sequencer. Defaults to None.
        """
        if not hasattr(self, parameter.value):
            super().setup(parameter, value, channel_id)
            return
        setattr(self, parameter.value, value)
        getattr(self.device, parameter.value)(value=value)
