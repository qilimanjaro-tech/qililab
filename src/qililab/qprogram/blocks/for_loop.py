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


from qililab.qprogram.blocks.block import Block
from qililab.qprogram.variable import Variable
from qililab.yaml import yaml


@yaml.register_class
class ForLoop(Block):
    def __init__(self, variable: Variable, start: int | float, stop: int | float, step: int | float) -> None:
        super().__init__()
        self.variable: Variable = variable
        self.start: int | float = start
        self.stop: int | float = stop
        self.step: int | float = step
