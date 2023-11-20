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

from qililab.instruments.awg_settings import AWGQbloxSequencer  # pylint: disable=cyclic-import
from qililab.instruments.instrument import Instrument, ParameterNotFound  # pylint: disable=cyclic-import
from qililab.instruments.utils.instrument_factory import InstrumentFactory  # pylint: disable=cyclic-import
from qililab.typings import InstrumentName, Parameter

from .qblox_qcm import QbloxQCM


@InstrumentFactory.register
class QbloxQCMRF(QbloxQCM):
    """Qblox QCM-RF driver."""

    name = InstrumentName.QCMRF

    @dataclass
    class QbloxQCMRFSettings(QbloxQCM.QbloxQCMSettings):  # pylint: disable=too-many-instance-attributes
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
            if channel_id is not None:
                sequencer: AWGQbloxSequencer = self._get_sequencer_by_id(channel_id)
            elif port_id is not None:
                sequencer = self.get_sequencers_from_chip_port_id(chip_port_id=port_id)[0]
            else:
                raise ParameterNotFound(
                    "`channel_id` cannot be None when setting the `LO_FREQUENCY` parameter."
                    "Please specify the sequencer index or use the specific Qblox parameter."
                )

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

    def get(self, parameter: Parameter, channel_id: int | None = None, port_id: str | None = None):
        """Set a parameter of the Qblox QCM-RF module.

        Args:
            parameter (Parameter): Parameter name.
            value (float | str | bool): Value to set.
            channel_id (int | None, optional): ID of the sequencer. Defaults to None.
        """
        if parameter == Parameter.LO_FREQUENCY:
            if channel_id is not None:
                sequencer: AWGQbloxSequencer = self._get_sequencer_by_id(channel_id)
            elif port_id is not None:
                sequencer = self.get_sequencers_from_chip_port_id(chip_port_id=port_id)[0]
            else:
                raise ParameterNotFound(
                    "`channel_id` cannot be None when setting the `LO_FREQUENCY` parameter."
                    "Please specify the sequencer index or use the specific Qblox parameter."
                )
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
            return getattr(self.settings, parameter.value)
        return super().get(parameter, channel_id)

    def to_dict(self):
        """Return a dict representation of an `QCM-RF` instrument."""
        dictionary = super().to_dict()
        dictionary.pop("out_offsets")
        return dictionary
