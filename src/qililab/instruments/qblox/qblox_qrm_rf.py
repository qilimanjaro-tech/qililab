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

from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.instruments.qblox.qblox_module import QbloxReadoutModule
from qililab.runcard.runcard_instruments import QbloxQRMRFRuncardInstrument, RuncardInstrument
from qililab.settings.instruments import QbloxADCSequencerSettings, QbloxQRMRFSettings


@InstrumentFactory.register(InstrumentType.QBLOX_QRM_RF)
class QbloxQRMRF(QbloxReadoutModule[QbloxQRMRFSettings]):
    @classmethod
    def get_default_settings(cls) -> QbloxQRMRFSettings:
        return QbloxQRMRFSettings(
            alias="qrm-rf", channels=[QbloxADCSequencerSettings(id=index) for index in range(6)]
        )

    def to_runcard(self) -> RuncardInstrument:
        return QbloxQRMRFRuncardInstrument(settings=self.settings)

    def initial_setup(self):
        super().initial_setup()

        # Set outputs
        for output in self.settings.outputs:
            self._set_output_lo_enabled(value=output.lo_enabled, output=output.port)
            self._set_output_lo_frequency(value=output.lo_frequency, output=output.port)
            self._set_output_attenuation(value=output.attenuation, output=output.port)
            self._set_output_offset_i(value=output.offset_i, output=output.port)
            self._set_output_offset_q(value=output.offset_q, output=output.port)

        # Set inputs
        for module_input in self.settings.inputs:
            self._set_input_attenuation(value=module_input.attenuation, module_input=module_input.port)
            self._set_input_offset_i(value=module_input.offset_i, module_input=module_input.port)
            self._set_input_offset_q(value=module_input.offset_q, module_input=module_input.port)

    def _map_output_connections(self):
        self.device.disconnect_outputs()

        for channel in self.settings.channels:
            operations = {
                0: self.device.sequencers[channel.id].connect_out0,
            }
            output = channel.outputs[0]
            operations[output]("IQ")

    def _map_input_connections(self):
        self.device.disconnect_inputs()

        for channel in self.settings.channels:
            operations = {
                0: self.device.channels[channel.id].connect_acq,
            }
            module_input = channel.inputs[0]
            operations[module_input]("in0")

    def _get_output_lo_enabled(self, output: int):
        operations = {
            0: self.device.out0_in0_lo_en,
        }
        operations[output]()

    def _set_output_lo_enabled(self, value: bool, output: int):
        operations = {
            0: self.device.out0_in0_lo_en,
        }
        operations[output](value)

    def _get_output_lo_frequency(self, output: int):
        operations = {
            0: self.device.out0_in0_lo_freq,
        }
        operations[output]()

    def _set_output_lo_frequency(self, value: float, output: int):
        operations = {
            0: self.device.out0_in0_lo_freq,
        }
        operations[output](value)

    def _get_output_attenuation(self, output: int):
        operations = {
            0: self.device.out0_att,
        }
        operations[output]()

    def _set_output_attenuation(self, value: float, output: int):
        operations = {
            0: self.device.out0_att,
        }
        operations[output](value)

    def _get_output_offset_i(self, output: int):
        operations = {
            0: self.device.out0_offset_path0,
        }
        operations[output]()

    def _set_output_offset_i(self, value: float, output: int):
        operations = {
            0: self.device.out0_offset_path0,
        }
        operations[output](value)

    def _get_output_offset_q(self, output: int):
        operations = {
            0: self.device.out0_offset_path1,
        }
        operations[output]()

    def _set_output_offset_q(self, value: float, output: int):
        operations = {
            0: self.device.out0_offset_path1,
        }
        operations[output](value)

    def _get_input_attenuation(self, module_input: int):
        operations = {
            0: self.device.in0_att,
        }
        operations[module_input]()

    def _set_input_attenuation(self, value: float, module_input: int):
        operations = {
            0: self.device.in0_att,
        }
        operations[module_input](value)

    def _get_input_offset_i(self, module_input: int):
        operations = {
            0: self.device.in0_offset_path0,
        }
        operations[module_input]()

    def _set_input_offset_i(self, value: float, module_input: int):
        operations = {
            0: self.device.in0_offset_path0,
        }
        operations[module_input](value)

    def _get_input_offset_q(self, module_input: int):
        operations = {
            0: self.device.in0_offset_path1,
        }
        operations[module_input]()

    def _set_input_offset_q(self, value: float, module_input: int):
        operations = {
            0: self.device.in0_offset_path1,
        }
        operations[module_input](value)
