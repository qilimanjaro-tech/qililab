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
from qililab.instruments.qblox_module import QbloxControlModule
from qililab.runcard.runcard_instruments import QbloxQCMRFRuncardInstrument, RuncardInstrument
from qililab.settings.instruments import QbloxQCMRFSettings, QbloxSequencerSettings


@InstrumentFactory.register(InstrumentType.QBLOX_QCM_RF)
class QbloxQCMRF(QbloxControlModule[QbloxQCMRFSettings]):
    @classmethod
    def get_default_settings(cls) -> QbloxQCMRFSettings:
        return QbloxQCMRFSettings(alias="qcm-rf", channels=[QbloxSequencerSettings(id=index) for index in range(6)])
    
    def to_runcard(self) -> RuncardInstrument:
        return QbloxQCMRFRuncardInstrument(settings=self.settings)

    def initial_setup(self):
        super().initial_setup()

        for output in self.settings.outputs:
            self._set_output_lo_enabled(value=output.lo_enabled, output=output.port)
            self._set_output_lo_frequency(value=output.lo_frequency, output=output.port)
            self._set_output_attenuation(value=output.attenuation, output=output.port)
            self._set_output_offset_i(value=output.offset_i, output=output.port)
            self._set_output_offset_q(value=output.offset_q, output=output.port)

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

    def _get_output_lo_enabled(self, output: int):
        operations = {0: self.device.out0_lo_en, 1: self.device.out1_lo_en}
        return operations[output]()

    def _set_output_lo_enabled(self, value: bool, output: int):
        operations = {0: self.device.out0_lo_en, 1: self.device.out1_lo_en}
        operations[output](value)

    def _get_output_lo_frequency(self, output: int):
        operations = {0: self.device.out0_lo_freq, 1: self.device.out1_lo_freq}
        return operations[output]()

    def _set_output_lo_frequency(self, value: float, output: int):
        operations = {0: self.device.out0_lo_freq, 1: self.device.out1_lo_freq}
        operations[output](value)

    def _get_output_attenuation(self, output: int):
        operations = {0: self.device.out0_att, 1: self.device.out1_att}
        return operations[output]()

    def _set_output_attenuation(self, value: float, output: int):
        operations = {0: self.device.out0_att, 1: self.device.out1_att}
        operations[output](value)

    def _get_output_offset_i(self, output: int):
        operations = {0: self.device.out0_offset_path0, 1: self.device.out1_offset_path0}
        return operations[output]()

    def _set_output_offset_i(self, value: float, output: int):
        operations = {0: self.device.out0_offset_path0, 1: self.device.out1_offset_path0}
        operations[output](value)

    def _get_output_offset_q(self, output: int):
        operations = {0: self.device.out0_offset_path1, 1: self.device.out1_offset_path1}
        return operations[output]()

    def _set_output_offset_q(self, value: float, output: int):
        operations = {0: self.device.out0_offset_path1, 1: self.device.out1_offset_path1}
        operations[output](value)
