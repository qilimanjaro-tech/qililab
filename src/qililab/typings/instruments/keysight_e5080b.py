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

"""Class Keysight E5080B"""

from qililab.instruments.keysight.driver_keysight_e5080b import Driver_KeySight_E5080B
from qililab.typings.instruments.device import Device


class KeysightE5080B(Driver_KeySight_E5080B, Device):
    """Typing class of the QCoDeS driver for the Keysight e5080b VNA."""
