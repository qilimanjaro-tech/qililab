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

from pydantic import model_validator

from qililab.settings.controllers.controller_settings import ControllerSettings


class QbloxClusterModule(str, Enum):
    QCM = "QCM"
    QRM = "QRM"
    QCM_RF = "QCM-RF"
    QRM_RF = "QRM-RF"


class QbloxClusterControllerSettings(ControllerSettings):
    NUMBER_OF_MODULES: ClassVar[int] = 20

    modules: dict[int, QbloxClusterModule]

    @model_validator(mode="after")
    def validate_modules(self):
        if len(self.modules) > self.NUMBER_OF_MODULES:
            raise ValueError(f"{self.__class__.__name__} supports up to {self.NUMBER_OF_MODULES} modules.")
        return self
