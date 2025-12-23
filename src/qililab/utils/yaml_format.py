# Copyright 2024 Qilimanjaro Quantum Tech
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

import types

from ruamel.yaml import YAML

from qililab.core.variables import Domain, Variable
from qililab.typings.enums import Parameter
from qililab.yaml import lambda_constructor, lambda_representer


def restate_lambda_constructor(yaml: YAML):
    yaml.representer.add_representer(types.LambdaType, lambda_representer)
    yaml.constructor.add_constructor("!lambda", lambda_constructor)
    yaml.register_class(Domain)
    yaml.register_class(Variable)
    yaml.register_class(Parameter)
