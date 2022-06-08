"""Yaml with int and float representers that convrt small/big values to scientific notation."""
import yaml

from qililab.utils import yaml_representer

yaml.add_representer(float, yaml_representer)
yaml.add_representer(int, yaml_representer)
