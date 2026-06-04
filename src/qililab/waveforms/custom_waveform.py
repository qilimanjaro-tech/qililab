import inspect
import types
from typing import Optional

from qililab.utils.derived_class import DerivedObject
from qililab.waveforms import Waveform
from qililab.yaml import yaml


@yaml.register_class
class CustomWaveform(DerivedObject):
    tag = "CustomWaveform"

    def __new__(cls, waveform_type: type = Waveform, name: Optional[str] = None, **transforms):
        if "transforms" in transforms:
            callable_transforms = transforms["transforms"]
            del transforms["transforms"]
        else:
            callable_transforms = {k: fn for k, fn in transforms.items() if isinstance(fn, (types.LambdaType, types.FunctionType))}

        cls._validate_transforms(callable_transforms)

        non_callables = {k: v for k, v in transforms.items() if not isinstance(v, (types.LambdaType, types.FunctionType))}

        def __init__(self, **kwargs):
            missing = set(non_callables) - set(kwargs)
            if missing:
                raise TypeError(f"Missing required parameters: {sorted(missing)}.")
            object.__setattr__(self, 'transforms', callable_transforms)
            object.__setattr__(self, 'waveform_type', waveform_type)
            if name is not None:
                object.__setattr__(self, 'name', name)
            for k, v in kwargs.items():
                object.__setattr__(self, k, v)

        props = {
            attr: cls._make_method(fn, force_method=(attr == "get_duration"))
            for attr, fn in callable_transforms.items()
        }
        props["__init__"] = __init__

        class_name = name or cls.tag
        DerivedClass = type(class_name, (waveform_type,), props)

        obj = object.__new__(DerivedClass)
        obj.__init__(**non_callables)
        yaml.representer.add_representer(obj.__class__, cls.to_yaml)
        return obj

    @staticmethod
    def _format_sig(args, defaults):
        defaults = defaults or ()
        n_no_default = len(args) - len(defaults)
        parts = [
            arg if i < n_no_default else f"{arg}={defaults[i - n_no_default]!r}"
            for i, arg in enumerate(args)
        ]
        return f"({', '.join(parts)})"

    @staticmethod
    def _validate_transforms(callable_transforms: dict):
        if "envelope" not in callable_transforms:
            raise ValueError("All Waveforms need an 'envelope'.")
        envelope_spec = inspect.getfullargspec(callable_transforms["envelope"])
        defaults = dict(zip(reversed(envelope_spec.args), reversed(envelope_spec.defaults or ())))
        if envelope_spec.args != ["self", "resolution"] or defaults.get("resolution") != 1:
            raise ValueError(
                f"'envelope' must have signature (self, resolution=1), "
                f"got {CustomWaveform._format_sig(envelope_spec.args, envelope_spec.defaults)}."
            )
        if "get_duration" in callable_transforms:
            get_duration_spec = inspect.getfullargspec(callable_transforms["get_duration"])
            if get_duration_spec.args != ["self"]:
                raise ValueError(
                    f"'get_duration' must have signature (self), "
                    f"got {CustomWaveform._format_sig(get_duration_spec.args, get_duration_spec.defaults)}."
                )

    @staticmethod
    def _make_method(function, force_method=False):
        signature = inspect.getfullargspec(function)
        sig_args = signature.args
        if not force_method and len(sig_args) == 1 and sig_args[0] == "self":
            return property(lambda self: function(self))
        def method(self, *args, **kwargs):
            bound = []
            args_iter = iter(args)
            for arg in sig_args:
                if arg == "self":
                    bound.append(self)
                else:
                    try:
                        bound.append(next(args_iter))
                    except StopIteration:
                        break  # remaining params use their defaults
            return function(*bound, **kwargs)
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
