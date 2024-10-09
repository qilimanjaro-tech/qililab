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


from qililab.qprogram.operations.operation import Operation
from qililab.yaml import yaml


@yaml.register_class
class SetOffset(Operation):
    def __init__(self, bus: str, offset_path0: float, offset_path1: float | None = None):
        super().__init__()
        self.bus: str = bus
        self.offset_path0: float = offset_path0
        self.offset_path1: float | None = offset_path1
