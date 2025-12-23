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
from collections import deque
from uuid import UUID

import numpy as np
from dill import dumps, loads  # noqa: S403
from ruamel.yaml import YAML


def ndarray_representer(representer, data):
    """Representer for ndarray"""
    value = {"dtype": str(data.dtype), "shape": data.shape, "data": data.ravel().tolist()}
    return representer.represent_mapping("!ndarray", value)


def ndarray_constructor(constructor, node):
    """Constructor for ndarray"""
    mapping = constructor.construct_mapping(node, deep=True)
    dtype = np.dtype(mapping["dtype"])
    shape = tuple(mapping["shape"])
    data = mapping["data"]
    return np.array(data, dtype=dtype).reshape(shape)


def deque_representer(representer, data):
    """Representer for deque"""
    return representer.represent_sequence("!deque", list(data))


def deque_constructor(constructor, node):
    """Constructor for ndarray"""
    return deque(constructor.construct_sequence(node))


def lambda_representer(representer, data):
    """Represent a lambda function by serializing its code."""
    serialized_lambda = base64.b64encode(dumps(data)).decode("utf-8")
    return representer.represent_scalar("!lambda", serialized_lambda)


def lambda_constructor(constructor, node):
    """Reconstruct a lambda function from the serialized data."""
    # Decode the base64-encoded string and load the lambda function
    serialized_lambda = base64.b64decode(node.value)
    return loads(serialized_lambda)  # noqa: S301


yaml = YAML(typ="unsafe")
yaml.register_class(UUID)
yaml.representer.add_representer(np.ndarray, ndarray_representer)
yaml.constructor.add_constructor("!ndarray", ndarray_constructor)
yaml.representer.add_representer(deque, deque_representer)
yaml.constructor.add_constructor("!deque", deque_constructor)
yaml.representer.add_representer(types.LambdaType, lambda_representer)
yaml.constructor.add_constructor("!lambda", lambda_constructor)


def restate_lambda_constructor(yaml: YAML):
    yaml.representer.add_representer(types.LambdaType, lambda_representer)
    yaml.constructor.add_constructor("!lambda", lambda_constructor)
