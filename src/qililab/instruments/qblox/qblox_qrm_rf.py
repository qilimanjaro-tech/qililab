"""This file contains the QbloxQCMRF class."""
from dataclasses import dataclass

from qililab.instruments import Instrument
from qililab.instruments.utils.instrument_factory import InstrumentFactory
from qililab.typings import InstrumentName, Parameter

from .qblox_qrm import QbloxQRM


@InstrumentFactory.register
class QbloxQRMRF(QbloxQRM):
    """Qblox QRM-RF driver."""

    name = InstrumentName.QRMRF

    @dataclass
    class QbloxQRMRFSettings(QbloxQRM.QbloxQRMSettings):
        """Contains the settings of a specific Qblox QRM-RF module."""

        out0_in0_lo_freq: float
        out0_in0_lo_en: bool
        out0_att: int  # must be a multiple of 2!
        in0_att: int  # must be a multiple of 2!
        out0_offset_path0: float
        out0_offset_path1: float

    settings: QbloxQRMRFSettings

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Initial setup"""
        super().initial_setup()
        # TODO: We should separate instrument settings and instrument parameters, such that the user can quickly get
        # al the settable parameters of an instrument.
        parameters = {
            "out0_in0_lo_freq",
            "out0_in0_lo_en",
            "out0_att",
            "in_0_att",
            "out0_offset_path0",
            "out0_offset_path1",
        }
        for parameter in parameters:
            self.setup(Parameter(parameter), getattr(self.settings, parameter))

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set a parameter of the Qblox QCM-RF module.
        Args:
            parameter (Parameter): Parameter name.
            value (float | str | bool): Value to set.
            channel_id (int | None, optional): ID of the sequencer. Defaults to None.
        """
        if not hasattr(self.settings, parameter.value):
            super().setup(parameter, value, channel_id)
            return
        setattr(self.settings, parameter.value, value)
        self.device.set(parameter.value, value)
