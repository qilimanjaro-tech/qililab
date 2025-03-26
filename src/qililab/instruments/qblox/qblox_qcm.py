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
from qililab.instruments.qblox.qblox_module import QbloxControlModule
from qililab.runcard.runcard_instruments import QbloxQCMRuncardInstrument, RuncardInstrument
from qililab.settings.instruments import QbloxQCMSettings, QbloxSequencerSettings


@InstrumentFactory.register(InstrumentType.QBLOX_QCM)
class QbloxQCM(QbloxControlModule[QbloxQCMSettings]):
    @classmethod
    def get_default_settings(cls) -> QbloxQCMSettings:
        return QbloxQCMSettings(
            alias="qcm",
            channels=[
                QbloxSequencerSettings(
                    id=index, outputs=[index], hardware_modulation=False, intermediate_frequency=None, gain_q=0
                )
                for index in range(4)
            ],
        )

    def to_runcard(self) -> RuncardInstrument:
        return QbloxQCMRuncardInstrument(settings=self.settings)

    def initial_setup(self):
        super().initial_setup()

        for output in self.settings.outputs:
            self.add_output_parameter(
                output_id=output.port,
                name="output_offset",
                settings_field="output_offset",
                get_device_value=self._get_output_offset,
                set_device_value=self._set_output_offset,
            )

            self._set_output_offset(value=output.offset, output=output.port)

    def _map_output_connections(self):
        """Disable all connections and map channels paths with output channels."""
        self.device.disconnect_outputs()

        for channel in self.settings.channels:
            operations = {
                0: self.device.sequencers[channel.id].connect_out0,
                1: self.device.sequencers[channel.id].connect_out1,
                2: self.device.sequencers[channel.id].connect_out2,
                3: self.device.sequencers[channel.id].connect_out3,
            }
            for output, path in zip(channel.outputs, ["I", "Q"]):
                operations[output](path)

    def _get_output_offset(self, output: int):
        operations = {
            0: self.device.out0_offset,
            1: self.device.out1_offset,
            2: self.device.out2_offset,
            3: self.device.out3_offset,
        }
        return operations[output]()

    def _set_output_offset(self, value: float, output: int):
        operations = {
            0: self.device.out0_offset,
            1: self.device.out1_offset,
            2: self.device.out2_offset,
            3: self.device.out3_offset,
        }
        operations[output](value)

    def is_awg(self) -> bool:
        return True
