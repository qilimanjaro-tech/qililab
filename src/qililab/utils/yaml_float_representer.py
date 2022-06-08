"""Yaml utils."""
import yaml


def yaml_representer(dumper: yaml.Dumper, value: int | float):
    """Int or float representer used by YAML."""
    tag = "int" if isinstance(value, int) else "float"
    if value != value:
        text = ".nan"
    elif value == dumper.inf_value:
        text = ".inf"
    elif value == -dumper.inf_value:
        text = "-.inf"
    else:
        text = f"{value:g}"
        if "e" in text and "." not in text.split("e")[0]:
            # Add a decimal point if value is integer
            tag = "float"
            text = text.split("e")[0] + ".e" + "".join(text.split("e")[1:])
    return dumper.represent_scalar(tag=f"tag:yaml.org,2002:{tag}", value=text)
