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

from typing import Any, Callable

from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.instruments.qblox_module import QbloxControlModule
from qililab.runcard.runcard_instruments import QbloxQCMRFRuncardInstrument, RuncardInstrument
from qililab.settings.instruments import QbloxQCMRFSettings, QbloxRFOutputSettings, QbloxSequencerSettings
from qililab.typings.enums import Parameter


@InstrumentFactory.register(InstrumentType.QBLOX_QCM_RF)
class QbloxQCMRF(QbloxControlModule[QbloxQCMRFSettings, QbloxRFOutputSettings]):
    settings: QbloxQCMRFSettings

    @classmethod
    def get_default_settings(cls) -> QbloxQCMRFSettings:
        return QbloxQCMRFSettings(alias="qcm-rf", sequencers=[QbloxSequencerSettings(id=index) for index in range(6)])

    def initial_setup(self):
        super().initial_setup()

        for output in self.settings.outputs:
            self._on_output_lo_enabled_changed(value=output.lo_enabled, output=output.port)
            self._on_output_lo_frequency_changed(value=output.lo_frequency, output=output.port)
            self._on_output_attenuation_changed(value=output.attenuation, output=output.port)
            self._on_output_offset_i_changed(value=output.offset_i, output=output.port)
            self._on_output_offset_q_changed(value=output.offset_q, output=output.port)

    def _map_output_connections(self):
        """Disable all connections and map sequencer paths with output channels."""
        self.device.disconnect_outputs()

        for sequencer in self.settings.sequencers:
            operations = {
                0: self.device.sequencers[sequencer.id].connect_out0,
                1: self.device.sequencers[sequencer.id].connect_out1,
            }
            output = sequencer.outputs[0]
            operations[output]("IQ")

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
        operations = {0: self.device.out0_lo_en, 1: self.device.out1_lo_en}
        operations[output](value)

    def _on_output_lo_frequency_changed(self, value: float, output: int):
        operations = {0: self.device.out0_lo_freq, 1: self.device.out1_lo_freq}
        operations[output](value)

    def _on_output_attenuation_changed(self, value: float, output: int):
        operations = {0: self.device.out0_att, 1: self.device.out1_att}
        operations[output](value)

    def _on_output_offset_i_changed(self, value: float, output: int):
        operations = {0: self.device.out0_offset_path0, 1: self.device.out1_offset_path0}
        operations[output](value)

    def _on_output_offset_q_changed(self, value: float, output: int):
        operations = {0: self.device.out0_offset_path1, 1: self.device.out1_offset_path1}
        operations[output](value)

    def to_runcard(self) -> RuncardInstrument:
        return QbloxQCMRFRuncardInstrument(settings=self.settings)
