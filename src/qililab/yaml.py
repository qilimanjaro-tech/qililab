from collections import deque
from uuid import UUID

import numpy as np
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


yaml = YAML(typ="unsafe")
yaml.register_class(UUID)
yaml.representer.add_representer(np.ndarray, ndarray_representer)
yaml.constructor.add_constructor("!ndarray", ndarray_constructor)
yaml.representer.add_representer(deque, deque_representer)
yaml.constructor.add_constructor("!deque", deque_constructor)
