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

from qililab.instruments.instrument_type import InstrumentType
from qililab.settings.instruments import (
    QbloxQCMRFSettings,
    QbloxQCMSettings,
    QbloxQRMRFSettings,
    QbloxQRMSettings,
    QDevilQDAC2Settings,
    RohdeSchwarzSG100Settings,
)


class QDevilQDAC2RuncardInstrument(BaseModel):
    type: Literal[InstrumentType.QDEVIL_QDAC2] = InstrumentType.QDEVIL_QDAC2
    settings: QDevilQDAC2Settings


class RohdeSchwarzSG100RuncardInstrument(BaseModel):
    type: Literal[InstrumentType.ROHDE_SCHWARZ_SG100] = InstrumentType.ROHDE_SCHWARZ_SG100
    settings: RohdeSchwarzSG100Settings


class QbloxQCMRuncardInstrument(BaseModel):
    type: Literal[InstrumentType.QBLOX_QCM] = InstrumentType.QBLOX_QCM
    settings: QbloxQCMSettings


class QbloxQCMRFRuncardInstrument(BaseModel):
    type: Literal[InstrumentType.QBLOX_QCM_RF] = InstrumentType.QBLOX_QCM_RF
    settings: QbloxQCMRFSettings


class QbloxQRMRuncardInstrument(BaseModel):
    type: Literal[InstrumentType.QBLOX_QRM] = InstrumentType.QBLOX_QRM
    settings: QbloxQRMSettings


class QbloxQRMRFRuncardInstrument(BaseModel):
    type: Literal[InstrumentType.QBLOX_QRM_RF] = InstrumentType.QBLOX_QRM_RF
    settings: QbloxQRMRFSettings


# Discriminated Union for instruments
RuncardInstrument = Annotated[
    QDevilQDAC2RuncardInstrument
    | RohdeSchwarzSG100RuncardInstrument
    | QbloxQCMRuncardInstrument
    | QbloxQCMRFRuncardInstrument
    | QbloxQRMRuncardInstrument
    | QbloxQRMRFRuncardInstrument,
    Field(discriminator="type"),
]
