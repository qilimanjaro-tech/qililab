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

"""USBConnection class"""

from qililab.instrument_connections.connection import Connection
from qililab.typings import ConnectionName
from qililab.utils import Factory


@Factory.register
class USBConnection(Connection):
    """Class declaring the necessary attributes and methods for an USB connection."""

    name = ConnectionName.USB
