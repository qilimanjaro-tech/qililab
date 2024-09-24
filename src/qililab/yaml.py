import types
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


# Lambda representer: convert lambda to a string
def lambda_representer(representer, data):
    """Represent a lambda function by serializing its code."""
    code = data.__code__
    return representer.represent_mapping(
        "!lambda",
        {
            "args": code.co_varnames[: code.co_argcount],
            "code": code.co_code.hex(),  # Convert bytecode to hex string
            "consts": code.co_consts,  # Serialize constants
            "names": code.co_names,  # Serialize names
            "flags": code.co_flags,  # Serialize flags
        },
    )


# Lambda constructor: convert string back to lambda
def lambda_constructor(constructor, node):
    """Reconstruct a lambda function from the serialized data."""
    mapping = constructor.construct_mapping(node, deep=True)

    code_hex = mapping["code"]
    argnames = mapping["args"]
    consts = mapping.get("consts", ())
    names = mapping.get("names", ())
    flags = mapping.get("flags", 64)  # Example flag, adjust based on needs
    code_bytes = bytes.fromhex(code_hex)

    # Dynamically generate the function using Python 3.8+ specific CodeType arguments
    def create_lambda(argnames, code_bytes):
        exec_code = types.CodeType(
            len(argnames),  # argcount
            0,  # posonlyargcount (new in Python 3.8+)
            0,  # kwonlyargcount
            len(argnames),  # nlocals (should match the number of arguments)
            0,  # stacksize (default, adjust if needed)
            flags,  # flags
            code_bytes,  # bytecode (MUST be passed as bytes)
            consts,  # consts (tuple of constants)
            names,  # names (tuple of names used in the bytecode)
            tuple(argnames),  # varnames (convert argnames to tuple)
            "",  # filename (default, can be adjusted)
            "<lambda>",  # name (name of the function, here it's lambda)
            0,  # firstlineno
            b"",  # lnotab (empty)
            (),  # freevars (empty tuple)
            (),  # cellvars (empty tuple)
        )
        return types.FunctionType(exec_code, {})

    return create_lambda(argnames, code_bytes)


yaml = YAML(typ="unsafe")
yaml.register_class(UUID)
yaml.representer.add_representer(np.ndarray, ndarray_representer)
yaml.constructor.add_constructor("!ndarray", ndarray_constructor)
yaml.representer.add_representer(deque, deque_representer)
yaml.constructor.add_constructor("!deque", deque_constructor)
yaml.representer.add_representer(types.LambdaType, lambda_representer)
yaml.constructor.add_constructor("!lambda", lambda_constructor)
