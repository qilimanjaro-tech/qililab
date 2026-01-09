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
import base64
import types
from uuid import UUID

from dill import dumps, loads  # noqa: S403
from qilisdk.yaml import yaml


def function_representer(representer, data):
    """Represent a non-lambda function by serializing it."""
    serialized_function = base64.b64encode(dumps(data, recurse=True)).decode("utf-8")
    return representer.represent_scalar("!function", serialized_function)


def lambda_representer(representer, data):
    """Represent a lambda function by serializing its code."""
    serialized_lambda = base64.b64encode(dumps(data, recurse=False)).decode("utf-8")
    return representer.represent_scalar("!lambda", serialized_lambda)


def lambda_constructor(constructor, node):
    """Reconstruct a lambda function from the serialized data."""
    # Decode the base64-encoded string and load the lambda function
    serialized_lambda = base64.b64decode(node.value)
    return loads(serialized_lambda)  # noqa: S301


yaml.register_class(UUID)

# Add the function and lambda representers that are missing in QiliSDK
yaml.representer.add_representer(types.LambdaType, lambda_representer)
yaml.constructor.add_constructor("!lambda", lambda_constructor)
