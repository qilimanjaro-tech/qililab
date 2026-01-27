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

from qililab.core import Variable
from . import Operation
from qililab.typings.enums import Parameter
from qililab.yaml import yaml


@yaml.register_class
class GetParameter(Operation):
    def __init__(
        self,
        variable: Variable,
        alias: str,
        parameter: Parameter,
        channel_id: int | None = None,
        output_id: int | None = None,
    ) -> None:
        super().__init__()
        self.variable: Variable = variable
        self.alias: str = alias
        self.parameter: Parameter = parameter
        self.channel_id: int | None = channel_id
        self.output_id: int | None = output_id
