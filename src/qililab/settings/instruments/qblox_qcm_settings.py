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
    QbloxControlModuleSettings,
    QbloxLFOutputSettings,
    QbloxRFOutputSettings,
)


class QbloxQCMSettings(QbloxControlModuleSettings[QbloxLFOutputSettings]):
    outputs: list[QbloxLFOutputSettings] = Field(default=[QbloxLFOutputSettings(port=index) for index in range(4)])

    @model_validator(mode="after")
    def validate_outputs(self):
        if (
            not self.outputs
            or len(self.outputs) != 4
            or any(output.port not in {0, 1, 2, 3} for output in self.outputs)
        ):
            raise ValueError("Qblox QCM should have exactly four outputs with ports 0, 1, 2, and 3.")
        for channel in self.channels:
            if not channel.outputs or len(channel.outputs) not in {1, 2}:
                raise ValueError("Qblox QCM sequencers should be connected to one or two outputs.")
            if any(output not in {0, 1, 2, 3} for output in channel.outputs):
                raise ValueError("Qblox QCM sequencer outputs should be one of {0, 1, 2, 3}.")
        return self


class QbloxQCMRFSettings(QbloxControlModuleSettings[QbloxRFOutputSettings]):
    outputs: list[QbloxRFOutputSettings] = Field(default=[QbloxRFOutputSettings(port=index) for index in range(2)])

    @model_validator(mode="after")
    def validate_outputs(self):
        if not self.outputs or len(self.outputs) != 2 or any(output.port not in {0, 1} for output in self.outputs):
            raise ValueError("Qblox QCM-RF should have exactly two outputs with ports 0 and 1.")
        for channel in self.channels:
            if not channel.outputs or len(channel.outputs) != 1:
                raise ValueError("Qblox QCM-RF sequencers should be connected to one output.")
            if any(output not in {0, 1} for output in channel.outputs):
                raise ValueError("Qblox QCM-RF sequencer outputs should be one of {0, 1}.")
        return self
