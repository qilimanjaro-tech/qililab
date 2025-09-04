# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This file contains the QbloxQCMRF class."""

from dataclasses import dataclass, field
from typing import ClassVar, Optional, Sequence

from qblox_instruments.qcodes_drivers.module import Module as QcmQrm

from qililab.instruments.decorators import check_device_initialized, log_set_parameter
from qililab.instruments.qblox.qblox_filters import QbloxFilter
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import ChannelID, InstrumentName, OutputID, Parameter, ParameterValue

from .qblox_qrm import QbloxQRM


@InstrumentFactory.register
class QbloxQRMRF(QbloxQRM):
    """Qblox QRM-RF driver."""

    name = InstrumentName.QRMRF
    device: QcmQrm

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
        out0_in0_lo_freq_cal_type_default: Optional[str] = "off"
        filters: Sequence[QbloxFilter] = field(
            init=False,
            default_factory=list,  # QCM-RF module doesn't have filters
        )

    # TODO: We should separate instrument settings and instrument parameters, such that the user can quickly get
    # al the settable parameters of an instrument.
    parameters: ClassVar[set[Parameter]] = {
        Parameter.OUT0_IN0_LO_FREQ,
        Parameter.OUT0_IN0_LO_EN,
        Parameter.OUT0_ATT,
        Parameter.IN0_ATT,
        Parameter.OUT0_OFFSET_PATH0,
        Parameter.OUT0_OFFSET_PATH1,
        Parameter.OUT0_IN0_LO_FREQ_CAL_TYPE_DEFAULT,
    }

    settings: QbloxQRMRFSettings

    @check_device_initialized
    def initial_setup(self):
        """Initial setup"""
        super().initial_setup()
        for parameter in self.parameters:
            self.set_parameter(parameter, getattr(self.settings, parameter.value))

    def _map_connections(self):
        """Disable all connections and map sequencer paths with output/input channels."""
        # Disable all connections
        self.device.disconnect_outputs()
        self.device.disconnect_inputs()

        for sequencer_dataclass in self.awg_sequencers:
            sequencer = self.device.sequencers[sequencer_dataclass.identifier]
            sequencer.connect_out0("IQ")
            sequencer.connect_acq("in0")

    @log_set_parameter
    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel_id: ChannelID | None = None, output_id: OutputID | None = None):
        """Set a parameter of the Qblox QCM-RF module.
        Args:
            parameter (Parameter): Parameter name.
            value (float | str | bool): Value to set.
            channel_id (int, optional): ID of the sequencer. Defaults to None.
        """
        if parameter == Parameter.LO_FREQUENCY:
            value = int(value)
            parameter = Parameter.OUT0_IN0_LO_FREQ

        if parameter == Parameter.OUT0_ATT:
            value = int(value)
            if self.is_device_active():
                max_att = self.device._get_max_out_att_0()
                if value > max_att:
                    raise Exception(
                        f"`{Parameter.OUT0_ATT}` for this module cannot be higher than {max_att}dB.\n"
                        "Please specify an attenuation level, multiple of 2, below this value."
                    )

        if parameter in self.parameters:
            setattr(self.settings, parameter.value, value)

            if self.is_device_active():
                self.device.set(parameter.value, value)
            return
        super().set_parameter(parameter, value, channel_id, output_id)

    def get_parameter(
        self, parameter: Parameter, channel_id: ChannelID | None = None, output_id: OutputID | None = None
    ):
        """Get a parameter of the Qblox QRM-RF module.
        Args:
            parameter (Parameter): Parameter name.
            value (float | str | bool): Value to set.
            channel_id (int, optional): ID of the sequencer. Defaults to None.
        """
        if parameter == Parameter.LO_FREQUENCY:
            parameter = Parameter.OUT0_IN0_LO_FREQ

        if parameter in self.parameters:
            return getattr(self.settings, parameter.value)
        return super().get_parameter(parameter, channel_id, output_id)

    def to_dict(self):
        """Return a dict representation of an `QRM-RF` instrument."""
        dictionary = super().to_dict()
        dictionary.pop("out_offsets")
        dictionary.pop("filters")
        return dictionary

    def calibrate_mixers(self, cal_type: str, channel_id: ChannelID | None = None):
        if cal_type == "lo":
            self.device._run_mixer_lo_calib(channel_id)
        elif cal_type == "lo_and_sidebands":
            self.device._run_mixer_lo_calib(channel_id)
            for sequencer_dataclass in self.awg_sequencers:
                sequencer = self.device.sequencers[sequencer_dataclass.identifier]
                sequencer.sideband_cal()
        else:
            raise Exception(
                f"`{cal_type}` for this module must be one of the following values: " "'lo' or 'lo_and_sidebands'."
            )

        return
