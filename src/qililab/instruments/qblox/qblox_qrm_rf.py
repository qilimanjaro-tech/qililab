"""This file contains the QbloxQCMRF class."""
from dataclasses import dataclass, field

from qililab.instruments import Instrument
from qililab.instruments.awg_settings import AWGQbloxADCSequencer
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
        out_offsets: list[float] = field(init=False, default_factory=list)

    # TODO: We should separate instrument settings and instrument parameters, such that the user can quickly get
    # al the settable parameters of an instrument.
    parameters = {
        Parameter.OUT0_IN0_LO_FREQ,
        Parameter.OUT0_IN0_LO_EN,
        Parameter.OUT0_ATT,
        Parameter.IN0_ATT,
        Parameter.OUT0_OFFSET_PATH0,
        Parameter.OUT0_OFFSET_PATH1,
    }

    settings: QbloxQRMRFSettings

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
        if parameter == Parameter.LO_FREQUENCY:
            if channel_id is None:
                raise ValueError(
                    "`channel_id` cannot be None when setting the `LO_FREQUENCY` parameter."
                    "Please specify the sequencer index or use the specific Qblox parameter."
                )
            sequencer: AWGQbloxADCSequencer = self._get_sequencer_by_id(channel_id)
            # Remember that a set is ordered! Thus `{1, 0} == {0, 1}` returns True.
            # For this reason, the following checks also take into account swapped paths!
            if {sequencer.output_i, sequencer.output_q} == {0, 1}:
                output = 0
            elif {sequencer.output_i, sequencer.output_q} == {2, 3}:
                output = 1
            else:
                raise ValueError(
                    f"Cannot set the LO frequency of sequencer {channel_id} because it is connected to two LOs. "
                    f"The paths of the sequencer are mapped to outputs {sequencer.output_i} and {sequencer.output_q} "
                    "respectively."
                )
            parameter = Parameter(f"out{output}_lo_freq")

        if parameter in self.parameters:
            setattr(self.settings, parameter.value, value)
            self.device.set(parameter.value, value)
            return
        super().setup(parameter, value, channel_id)
