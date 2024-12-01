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
from __future__ import annotations

from typing import Any, Callable

from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.instruments.qblox_module import QbloxReadoutModule
from qililab.runcard.runcard_instruments import QbloxQRMRFRuncardInstrument, RuncardInstrument
from qililab.settings.instruments import (
    QbloxADCSequencerSettings,
    QbloxQRMRFSettings,
    QbloxRFInputSettings,
    QbloxRFOutputSettings,
)
from qililab.typings.enums import Parameter


@InstrumentFactory.register(InstrumentType.QBLOX_QRM_RF)
class QbloxQRMRF(QbloxReadoutModule[QbloxQRMRFSettings, QbloxRFOutputSettings, QbloxRFInputSettings]):
    settings: QbloxQRMRFSettings

    @classmethod
    def get_default_settings(cls) -> QbloxQRMRFSettings:
        return QbloxQRMRFSettings(
            alias="qrm-rf", sequencers=[QbloxADCSequencerSettings(id=index) for index in range(6)]
        )

    def to_runcard(self) -> RuncardInstrument:
        return QbloxQRMRFRuncardInstrument(settings=self.settings)

    def _map_output_connections(self):
        self.device.disconnect_outputs()

        for sequencer in self.settings.sequencers:
            operations = {
                0: self.device.sequencers[sequencer.id].connect_out0,
            }
            output = sequencer.outputs[0]
            operations[output]("IQ")

    def _map_input_connections(self):
        self.device.disconnect_inputs()

        for sequencer in self.settings.sequencers:
            operations = {
                0: self.device.sequencers[sequencer.id].connect_acq,
            }
            input = sequencer.inputs[0]
            operations[input]("in0")

    @classmethod
    def _output_parameter_to_settings(cls) -> dict[Parameter, str]:
        return super()._output_parameter_to_settings() | {
            Parameter.LO_ENABLED: "lo_enabled",
            Parameter.LO_FREQUENCY: "lo_frequency",
            Parameter.ATTENUATION: "attenuation",
            Parameter.OFFSET_I: "offset_i",
            Parameter.OFFSET_Q: "offset_q",
        }

    def _output_parameter_to_device_operation(self) -> dict[Parameter, Callable[..., Any]]:
        return super()._output_parameter_to_device_operation() | {
            Parameter.LO_ENABLED: self._on_output_lo_enabled_changed,
            Parameter.LO_FREQUENCY: self._on_output_lo_frequency_changed,
            Parameter.ATTENUATION: self._on_output_attenuation_changed,
            Parameter.OFFSET_I: self._on_output_offset_i_changed,
            Parameter.OFFSET_Q: self._on_output_offset_q_changed,
        }

    def _on_output_lo_enabled_changed(self, value: bool, output: int):
        operations = {
            0: self.device.out0_in0_lo_en,
        }
        operations[output](value)

    def _on_output_lo_frequency_changed(self, value: float, output: int):
        operations = {
            0: self.device.out0_in0_lo_freq,
        }
        operations[output](value)

    def _on_output_attenuation_changed(self, value: float, output: int):
        operations = {
            0: self.device.out0_att,
        }
        operations[output](value)

    def _on_output_offset_i_changed(self, value: float, output: int):
        operations = {
            0: self.device.out0_offset_path0,
        }
        operations[output](value)

    def _on_output_offset_q_changed(self, value: float, output: int):
        operations = {
            0: self.device.out0_offset_path1,
        }
        operations[output](value)

    @classmethod
    def _input_parameter_to_settings(cls) -> dict[Parameter, str]:
        return super()._input_parameter_to_settings() | {
            Parameter.ATTENUATION: "attenuation",
            Parameter.OFFSET_I: "offset_i",
            Parameter.OFFSET_Q: "offset_q",
        }

    def _input_parameter_to_device_operation(self) -> dict[Parameter, Callable[..., Any]]:
        return super()._input_parameter_to_device_operation() | {
            Parameter.ATTENUATION: self._on_input_attenuation_changed,
            Parameter.OFFSET_I: self._on_input_offset_i_changed,
            Parameter.OFFSET_Q: self._on_input_offset_q_changed,
        }

    def _on_input_attenuation_changed(self, value: float, input: int):
        operations = {
            0: self.device.in0_att,
        }
        operations[input](value)

    def _on_input_offset_i_changed(self, value: float, input: int):
        operations = {
            0: self.device.in0_offset_path0,
        }
        operations[input](value)

    def _on_input_offset_q_changed(self, value: float, input: int):
        operations = {
            0: self.device.in0_offset_path1,
        }
        operations[input](value)
