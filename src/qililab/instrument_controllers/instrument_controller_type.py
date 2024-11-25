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


class InstrumentControllerType(str, Enum):
    QBLOX_CLUSTER_CONTROLLER = "qblox_cluster_controller"
    QBLOX_SPI_RACK_CONTROLLER = "qblox_spi_rack_controller"
    QDEVIL_QDAC2_CONTROLLER = "qdac2_controller"
    ROHDE_SCHWARZ_SG100_CONTROLLER = "sg100_controller"
