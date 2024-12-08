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

from qililab.instruments.decorators import check_device_initialized
from qililab.instruments.instrument_factory import InstrumentFactory
from qililab.instruments.instrument_type import InstrumentType
from qililab.instruments.qblox_module import QbloxReadoutModule
from qililab.runcard.runcard_instruments import QbloxQRMRuncardInstrument, RuncardInstrument
from qililab.settings.instruments import (
    QbloxADCSequencerSettings,
    QbloxQRMSettings,
)


@InstrumentFactory.register(InstrumentType.QBLOX_QRM)
class QbloxQRM(QbloxReadoutModule[QbloxQRMSettings]):
    @classmethod
    def get_default_settings(cls) -> QbloxQRMSettings:
        return QbloxQRMSettings(alias="qrm", channels=[QbloxADCSequencerSettings(id=index) for index in range(6)])

    def to_runcard(self) -> RuncardInstrument:
        return QbloxQRMRuncardInstrument(settings=self.settings)

    @check_device_initialized
    def initial_setup(self):
        super().initial_setup()

        # Set outputs
        for output in self.settings.outputs:
            self._set_output_offset(value=output.offset, output=output.port)

        # Set inputs
        for input in self.settings.inputs:
            self._set_input_gain(value=input.gain, input=input.port)
            self._set_input_offset(value=input.offset, input=input.port)

    def _map_output_connections(self):
        """Disable all connections and map sequencer paths with output channels."""
        self.device.disconnect_outputs()

        for channel in self.settings.channels:
            operations = {
                0: self.device.sequencers[channel.id].connect_out0,
                1: self.device.sequencers[channel.id].connect_out1
            }
            for output, path in zip(channel.outputs, ["I", "Q"]):
                operations[output](path)

    def _map_input_connections(self):
        """Disable all connections and map sequencer paths with output channels."""
        self.device.disconnect_inputs()

        for sequencer in self.settings.channels:
            self.device.sequencers[sequencer.id].connect_acq_I("in0")
            self.device.sequencers[sequencer.id].connect_acq_Q("in1")

    def _get_output_offset(self, output: int):
        operations = {
            0: self.device.out0_offset,
            1: self.device.out1_offset,
        }
        return operations[output]()

    def _set_output_offset(self, value: float, output: int):
        operations = {
            0: self.device.out0_offset,
            1: self.device.out1_offset,
        }
        operations[output](value)

    def _get_input_gain(self, input: int):
        operations = {0: self.device.in0_gain, 1: self.device.in1_gain}
        return operations[input]()

    def _set_input_gain(self, value: float, input: int):
        operations = {0: self.device.in0_gain, 1: self.device.in1_gain}
        operations[input](value)

    def _get_input_offset(self, input: int):
        operations = {0: self.device.in0_offset, 1: self.device.in1_offset}
        operations[input]()

    def _set_input_offset(self, value: float, input: int):
        operations = {0: self.device.in0_offset, 1: self.device.in1_offset}
        operations[input](value)
