"""Yaml utils."""
from types import NoneType

import yaml


def yaml_representer(dumper: yaml.Dumper, value: int | float):
    """Int or float representer used by YAML."""
    tag = "int" if isinstance(value, int) else "float"
    text = f"{value:g}"
    if "e" in text and "." not in text.split("e")[0]:
        # Add a decimal point if value is integer
        tag = "float"
        text = text.split("e")[0] + ".e" + "".join(text.split("e")[1:])
    if "." not in text and tag == "float":
        # Change tag to int if there is no decimal point.
        tag = "int"
    return dumper.represent_scalar(tag=f"tag:yaml.org,2002:{tag}", value=text)


def null_representer(dumper: yaml.Dumper, value: NoneType):
    """Int or float representer used by YAML."""
    return dumper.represent_scalar(tag="tag:yaml.org,2002:null", value="")
