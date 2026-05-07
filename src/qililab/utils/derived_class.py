import base64
import inspect
import types

from dill import dumps, loads

from qililab.yaml import yaml


@yaml.register_class
class DerivedObject:
    tag = "DerivedObject"

    def __new__(cls, sources: dict[str, object] = {}, **transforms):
        if "transforms" in transforms:
            callable_transforms = transforms["transforms"]
            del transforms["transforms"]
        else:
            callable_transforms = {name: fn for name, fn in transforms.items() if isinstance(fn, (types.LambdaType, types.FunctionType))}

        props: dict[str, property] = {
            name: cls._make_method(sources, fn)
            for name, fn in callable_transforms.items()
        }
        def __getattr__(self, name):
            try:
                return object.__getattribute__(self, name)
            except AttributeError:
                sources = object.__getattribute__(self, 'sources')
                for source in sources.values():
                    if hasattr(source, name):
                        return getattr(source, name)
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        props['__getattr__'] = __getattr__

        source_class = tuple(type(obj) for obj in sources.values())
        DerivedClass = type(cls.tag, source_class, props)

        obj = object.__new__(DerivedClass)
        object.__setattr__(obj, 'sources', sources)
        for source_name, source_obj in sources.items():
            object.__setattr__(obj, source_name, source_obj)
        object.__setattr__(obj, 'transforms', callable_transforms)
        for name, value in transforms.items():
            if not isinstance(value, (types.LambdaType, types.FunctionType)):
                object.__setattr__(obj, name, value)
        yaml.representer.add_representer(obj.__class__, cls.to_yaml)
        return obj

    @staticmethod
    def _make_method(sources: dict[str, object], fn):
        signature = inspect.getfullargspec(fn)
        sig_args = signature.args
        sig_kwargs = signature.kwonlyargs
        sig_sources = ["self", *sources.keys()]
        if all(arg in sig_sources for arg in sig_args + sig_kwargs):
            return property(
                lambda self: fn(
                    **{arg: self if arg == "self"
                    else object.__getattribute__(self, arg)
                    for arg in sig_args + sig_kwargs}
                )
            )
        def method(self, *args, **kwargs):
            args = (a for a in args)
            return fn(
                *(next(args) if arg not in sig_sources
                else (self if arg == "self" else object.__getattribute__(self, arg))
                for arg in sig_args),
                **{kwarg: self if kwarg == "self"
                else object.__getattribute__(self, kwarg)
                for kwarg in sig_kwargs if kwarg in sig_sources},
                **kwargs
            )
        return method


    @classmethod
    def to_yaml(cls, representer, node):
        """Method to be called automatically during YAML serialization."""
        data = {key: value for key, value in node.__dict__.items() if not key.startswith('_')}
        sources = data["sources"].keys()
        for source in sources:
            del data[source]
        return representer.represent_mapping('!' + cls.tag, data)


    @classmethod
    def from_yaml(cls, constructor, node):
        """Method to be called automatically during YAML deserialization."""
        mapping = constructor.construct_mapping(node, deep=True)
        sources = mapping["sources"]
        del mapping["sources"]
        return cls(sources=sources, **mapping)

    def to_dict(self):
        data = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        data["transforms"] = {key: base64.b64encode(dumps(fn, recurse=True)).decode("utf-8") for key, fn in data["transforms"]}
        return data
