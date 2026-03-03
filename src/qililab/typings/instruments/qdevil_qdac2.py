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

"""Driver for QDevil QDAC-II"""
from qcodes_contrib_drivers.drivers.QDevil.QDAC2 import QDac2 as Driver_QDac2

from qililab.typings.instruments.device import Device


class QDevilQDac2(Driver_QDac2, Device):
    """Typing class of the QDevil QDAC-II."""
