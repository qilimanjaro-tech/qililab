"""This file contains the QbloxQCMRF class."""
from dataclasses import dataclass, field

from qililab.instruments import Instrument
from qililab.instruments.utils.instrument_factory import InstrumentFactory
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
        Parameter.OUT0_LO_FREQ,
        Parameter.OUT0_LO_EN,
        Parameter.OUT0_ATT,
        Parameter.OUT0_OFFSET_PATH0,
        Parameter.OUT0_OFFSET_PATH1,
        Parameter.OUT1_LO_FREQ,
        Parameter.OUT1_LO_EN,
        Parameter.OUT1_ATT,
        Parameter.OUT1_OFFSET_PATH0,
        Parameter.OUT1_OFFSET_PATH1,
    }

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Initial setup"""
        super().initial_setup()
        for parameter in self.parameters:
            self.setup(parameter, getattr(self.settings, parameter.value))

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set a parameter of the Qblox QCM-RF module.

        Args:
            parameter (Parameter): Parameter name.
            value (float | str | bool): Value to set.
            channel_id (int | None, optional): ID of the sequencer. Defaults to None.
        """
        if parameter in self.parameters:
            setattr(self.settings, parameter.value, value)
            self.device.set(parameter.value, value)
            return
        super().setup(parameter, value, channel_id)
