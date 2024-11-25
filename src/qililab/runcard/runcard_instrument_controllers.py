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

from qililab.instrument_controllers.instrument_controller_type import InstrumentControllerType
from qililab.settings.instrument_controllers import (
    QbloxClusterControllerSettings,
    QbloxSPIRackControllerSettings,
    QDevilQDAC2ControllerSettings,
    RohdeSchwarzSG100ControllerSettings,
)


class QbloxClusterRuncardInstrumentController(BaseModel):
    type: Literal[InstrumentControllerType.QBLOX_CLUSTER_CONTROLLER] = InstrumentControllerType.QBLOX_CLUSTER_CONTROLLER
    settings: QbloxClusterControllerSettings


class QbloxSPIRackRuncardInstrumentController(BaseModel):
    type: Literal[InstrumentControllerType.QBLOX_SPI_RACK_CONTROLLER] = (
        InstrumentControllerType.QBLOX_SPI_RACK_CONTROLLER
    )
    settings: QbloxSPIRackControllerSettings


class QDevilQDAC2RuncardInstrumentController(BaseModel):
    type: Literal[InstrumentControllerType.QDEVIL_QDAC2_CONTROLLER] = InstrumentControllerType.QDEVIL_QDAC2_CONTROLLER
    settings: QDevilQDAC2ControllerSettings


class RohdeSchwarzSG100RuncardInstrumentController(BaseModel):
    type: Literal[InstrumentControllerType.ROHDE_SCHWARZ_SG100_CONTROLLER] = (
        InstrumentControllerType.ROHDE_SCHWARZ_SG100_CONTROLLER
    )
    settings: RohdeSchwarzSG100ControllerSettings


# Discriminated Union for instruments
RuncardInstrumentController = Annotated[
    QbloxClusterRuncardInstrumentController
    | QbloxSPIRackRuncardInstrumentController
    | QDevilQDAC2RuncardInstrumentController
    | RohdeSchwarzSG100RuncardInstrumentController,
    Field(discriminator="type"),
]
