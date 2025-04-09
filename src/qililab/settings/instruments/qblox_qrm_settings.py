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

from pydantic import Field, model_validator

from qililab.settings.instruments.qblox_base_settings import (
    QbloxLFInputSettings,
    QbloxLFOutputSettings,
    QbloxReadoutModuleSettings,
    QbloxRFInputSettings,
    QbloxRFOutputSettings,
)


class QbloxQRMSettings(QbloxReadoutModuleSettings[QbloxLFOutputSettings, QbloxLFInputSettings]):
    outputs: list[QbloxLFOutputSettings] = Field(default=[QbloxLFOutputSettings(port=index) for index in range(2)])
    inputs: list[QbloxLFInputSettings] = Field(default=[QbloxLFInputSettings(port=index) for index in range(2)])

    @model_validator(mode="after")
    def validate_outputs(self):
        if not self.outputs or len(self.outputs) != 2 or any(output.port not in {0, 1} for output in self.outputs):
            raise ValueError("Qblox QRM should have exactly two outputs with ports 0 and 1.")
        for channel in self.channels:
            if not channel.outputs or len(channel.outputs) > 2:
                raise ValueError("Qblox QRM sequencers should be connected to one or two outputs.")
            if any(output not in {0, 1} for output in channel.outputs):
                raise ValueError("Qblox QRM-RF sequencer outputs should be one of {0, 1}.")
        return self

    @model_validator(mode="after")
    def validate_inputs(self):
        if not self.inputs or len(self.inputs) != 2 or any(input.port not in {0, 1} for input in self.inputs):
            raise ValueError("Qblox QRM should have exactly two inputs with ports 0 and 1.")
        for channel in self.channels:
            if not channel.outputs or len(channel.outputs) != 1:
                raise ValueError("Qblox QRM-RF sequencers should be connected to one input.")
            if any(output not in {0} for output in channel.outputs):
                raise ValueError("Qblox QRM-RF sequencer inputs should be one of {0}.")
        return self


class QbloxQRMRFSettings(QbloxReadoutModuleSettings[QbloxRFOutputSettings, QbloxRFInputSettings]):
    outputs: list[QbloxRFOutputSettings] = Field(default=[QbloxRFOutputSettings(port=0)])
    inputs: list[QbloxRFInputSettings] = Field(default=[QbloxRFInputSettings(port=0)])

    @model_validator(mode="after")
    def validate_outputs(self):
        if not self.outputs or len(self.outputs) != 1 or self.outputs[0].port != 0:
            raise ValueError("Qblox QRM-RF should have exactly one output with port 0.")
        for channel in self.channels:
            if not channel.outputs or len(channel.outputs) != 1:
                raise ValueError("Qblox QRM-RF sequencers should be connected to one output.")
            if any(output not in {0} for output in channel.outputs):
                raise ValueError("Qblox QRM-RF sequencer outputs should be one of {0}.")
        return self

    @model_validator(mode="after")
    def validate_inputs(self):
        if not self.inputs or len(self.inputs) != 1 or self.inputs[0].port != 0:
            raise ValueError("Qblox QRM-RF should have exactly one input with port 0.")
        for channel in self.channels:
            if not channel.inputs or len(channel.inputs) != 1:
                raise ValueError("Qblox QRM-RF sequencers should be connected to one input.")
            if any(input not in {0} for input in channel.inputs):
                raise ValueError("Qblox QRM-RF sequencer inputs should be one of {0}.")
        return self
