"""This file contains the QbloxQCMRF class."""
from dataclasses import dataclass, field

from qpysequence.program import Loop, Register
from qpysequence.weights import Weights

from qililab.instruments import Instrument
from qililab.instruments.awg_settings import AWGQbloxSequencer
from qililab.instruments.utils.instrument_factory import InstrumentFactory
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.typings import InstrumentName, Parameter

from .qblox_qcm import QbloxQCM


@InstrumentFactory.register
class QbloxQCMRF(QbloxQCM):
    """Qblox QCM-RF driver."""

    name = InstrumentName.QCMRF

    @dataclass
    class QbloxQCMRFSettings(QbloxQCM.QbloxQCMSettings):
        """Contains the settings of a specific Qblox QCM-RF module."""

        out0_lo_freq: float
        out0_lo_en: bool
        out0_att: int  # must be a multiple of 2!
        out0_offset_path0: float
        out0_offset_path1: float
        out1_lo_freq: float
        out1_lo_en: bool
        out1_att: int  # must be a multiple of 2!
        out1_offset_path0: float
        out1_offset_path1: float
        out_offsets: list[float] = field(
            init=False, default_factory=list  # QCM-RF module doesn't have an `out_offsets` parameter
        )

    settings: QbloxQCMRFSettings
    # TODO: We should separate instrument settings and instrument parameters, such that the user can quickly get
    # al the settable parameters of an instrument.
    parameters = {
        "out0_lo_freq",
        "out0_lo_en",
        "out0_att",
        "out0_offset_path0",
        "out0_offset_path1",
        "out1_lo_freq",
        "out1_lo_en",
        "out1_att",
        "out1_offset_path0",
        "out1_offset_path1",
    }

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Initial setup"""
        super().initial_setup()
        for parameter in self.parameters:
            self.setup(Parameter(parameter), getattr(self.settings, parameter))

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set a parameter of the Qblox QCM-RF module.

        Args:
            parameter (Parameter): Parameter name.
            value (float | str | bool): Value to set.
            channel_id (int | None, optional): ID of the sequencer. Defaults to None.
        """
        if parameter.value in self.parameters:
            setattr(self.settings, parameter.value, value)
            self.device.set(parameter.value, value)
            return
        super().setup(parameter, value, channel_id)
