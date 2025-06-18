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


from typing import Annotated, Literal

from pydantic import BaseModel, Field

from qililab.controllers.controller_type import ControllerType
from qililab.settings.controllers import QbloxClusterControllerSettings, QDevilQDAC2ControllerSettings


class QDevilQDAC2RuncardController(BaseModel):
    type: Literal[ControllerType.QDEVIL_QDAC2_CONTROLLER] = ControllerType.QDEVIL_QDAC2_CONTROLLER
    settings: QDevilQDAC2ControllerSettings


class QbloxClusterRuncardController(BaseModel):
    type: Literal[ControllerType.QBLOX_CLUSTER_CONTROLLER] = ControllerType.QBLOX_CLUSTER_CONTROLLER
    settings: QbloxClusterControllerSettings


# Discriminated Union for instruments
RuncardController = Annotated[
    QDevilQDAC2RuncardController | QbloxClusterRuncardController,
    Field(discriminator="type"),
]
