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

from qililab.instruments import Instrument  # pylint: disable=cyclic-import
from qililab.instruments.utils.instrument_factory import InstrumentFactory  # pylint: disable=cyclic-import
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
    def setup(
        self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None, port_id: str | None = None
    ):
        """Set a parameter of the Qblox QCM-RF module.
        Args:
            parameter (Parameter): Parameter name.
            value (float | str | bool): Value to set.
            channel_id (int | None, optional): ID of the sequencer. Defaults to None.
        """
        if parameter == Parameter.LO_FREQUENCY:
            parameter = Parameter.OUT0_IN0_LO_FREQ

        if parameter in self.parameters:
            setattr(self.settings, parameter.value, value)
            self.device.set(parameter.value, value)
            return
        super().setup(parameter, value, channel_id, port_id=port_id)

    def get(self, parameter: Parameter, channel_id: int | None = None, port_id: str | None = None):
        """Set a parameter of the Qblox QCM-RF module.
        Args:
            parameter (Parameter): Parameter name.
            value (float | str | bool): Value to set.
            channel_id (int | None, optional): ID of the sequencer. Defaults to None.
        """
        if parameter == Parameter.LO_FREQUENCY:
            parameter = Parameter.OUT0_IN0_LO_FREQ

        if parameter in self.parameters:
            return getattr(self.settings, parameter.value)
        return super().get(parameter, channel_id, port_id=port_id)

    def to_dict(self):
        """Return a dict representation of an `QRM-RF` instrument."""
        dictionary = super().to_dict()
        dictionary.pop("out_offsets")
        return dictionary
