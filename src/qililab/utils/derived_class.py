from qililab.yaml import yaml
import types

def represent_derived_object(representer, obj):
    """Serialize DerivedObject instances"""
    data = {key: value for key, value in obj.__dict__.items() if not key.startswith('_')}
    return representer.represent_mapping('!DerivedObject', data)

@yaml.register_class
class DerivedObject:
    yaml_tag = "!DerivedObject"

    def __new__(cls, *source_obj: tuple[type,...], **transforms):
        if "transforms" in transforms:
            callable_transforms = transforms["transforms"]
            del transforms["transforms"]
        else:
            callable_transforms = {name: fn for name, fn in transforms.items() if isinstance(fn, (types.LambdaType, types.FunctionType))}

        props: dict[str, property] = {
            name: property(lambda self, f=fn: f(*object.__getattribute__(self, 'source_obj')))
            for name, fn in callable_transforms.items() 
        }
        
        def __getattr__(self, name):
            try:
                print(name)
                return object.__getattribute__(self, name)
            except AttributeError:
                print(name)
                sources = object.__getattribute__(self, 'source_obj')
                for source in sources:
                    if hasattr(source, name):
                        return getattr(source, name)
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")        
        
        props['__getattr__'] = __getattr__
        
        source_class = tuple(type(obj) for obj in source_obj)
        DerivedClass = type("DerivedObject", source_class, props)
        
        obj = object.__new__(DerivedClass)
        object.__setattr__(obj, 'source_obj', source_obj)
        object.__setattr__(obj, 'transforms', callable_transforms)
        for name, value in transforms.items():
            if not isinstance(value, (types.LambdaType, types.FunctionType)):
                object.__setattr__(obj, name, value)
        yaml.representer.add_representer(obj.__class__, represent_derived_object)
        return obj

    @classmethod
    def to_yaml(cls, representer, node):
        """Method to be called automatically during YAML serialization."""
        return represent_derived_object(representer, node)

    @classmethod
    def from_yaml(cls, constructor, node):
        """Method to be called automatically during YAML deserialization."""
        mapping = constructor.construct_mapping(node, deep=True)
        source_obj = mapping["source_obj"]
        del mapping["source_obj"]
        return cls(*source_obj, **mapping)