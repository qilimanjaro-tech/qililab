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

from enum import Enum
from typing import ClassVar

from pydantic import Field, model_validator

from qililab.settings.settings import Settings


class ReferenceClock(str, Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"


class ConnectionType(str, Enum):
    TCP_IP = "tcp_ip"
    USB = "usb"


class ConnectionSettings(Settings):
    type: ConnectionType = Field(default=ConnectionType.TCP_IP)
    address: str = Field(default="168.0.0.1")


class InstrumentModule(Settings):
    alias: str
    slot: int


class InstrumentControllerSettings(Settings):
    """Base Settings for all Instruments"""

    alias: str
    connection: ConnectionSettings = Field(default=ConnectionSettings())
    modules: list[InstrumentModule] = Field(default=[])
    reset: bool = Field(default=True)

    NUMBER_OF_MODULES: ClassVar[int]

    @model_validator(mode="after")
    def validate_modules(self):
        if len(self.modules) > self.NUMBER_OF_MODULES:
            raise ValueError(f"{self.__class__.__name__} supports up to {self.NUMBER_OF_MODULES} modules.")
        return self
