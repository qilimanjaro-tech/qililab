import inspect
import types

from qililab.utils.derived_class import DerivedObject
from qililab.waveforms import Waveform
from qililab.yaml import yaml


@yaml.register_class
class CustomWaveform(DerivedObject):
    tag = "CustomWaveform"

    def __new__(cls, waveform_type: type = Waveform, **transforms):
        if "transforms" in transforms:
            callable_transforms = transforms["transforms"]
            del transforms["transforms"]
        else:
            callable_transforms = {name: fn for name, fn in transforms.items() if isinstance(fn, (types.LambdaType, types.FunctionType))}

        props: dict[str, property] = {
            name: cls._make_method(fn)
            for name, fn in callable_transforms.items()
        }

        DerivedClass = type(cls.tag, waveform_type, props)

        obj = object.__new__(DerivedClass)
        object.__setattr__(obj, 'transforms', callable_transforms)
        object.__setattr__(obj, 'waveform_type', waveform_type)
        for name, value in transforms.items():
            if not isinstance(value, (types.LambdaType, types.FunctionType)):
                object.__setattr__(obj, name, value)
        yaml.representer.add_representer(obj.__class__, cls.to_yaml)
        return obj

    @staticmethod
    def _make_method(fn):
        signature = inspect.getfullargspec(fn)
        sig_args = signature.args
        if len(sig_args) == 1 and sig_args[0] =="self":
            return property(lambda self: fn(self))
        def method(self, *args, **kwargs):
            args = (a for a in args)
            return fn(
                *(next(args) if arg != "self" else self
                for arg in sig_args),
                **kwargs
            )
        return method


    @classmethod
    def to_yaml(cls, representer, node):
        """Method to be called automatically during YAML serialization."""
        data = {key: value for key, value in node.__dict__.items() if not key.startswith('_')}
        return representer.represent_mapping('!' + cls.tag, data)

    @classmethod
    def from_yaml(cls, constructor, node):
        """Method to be called automatically during YAML deserialization."""
        return cls(**constructor.construct_mapping(node, deep=True))
