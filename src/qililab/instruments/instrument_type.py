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


class InstrumentType(str, Enum):
    QDEVIL_QDAC2 = "qdac2"
    ROHDE_SCHWARZ_SG100 = "sg100"
    QBLOX_QCM = "qcm"
    QBLOX_QRM = "qrm"
    QBLOX_QCM_RF = "qcm-rf"
    QBLOX_QRM_RF = "qrm-rf"
    QBLOX_S4G = "s4g"
    QBLOX_D5A = "d5a"
