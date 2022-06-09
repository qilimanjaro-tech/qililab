"""Yaml with int and float representers that convrt small/big values to scientific notation."""
from types import NoneType

import yaml

from qililab.utils import null_representer, yaml_representer

yaml.add_representer(float, yaml_representer)
yaml.add_representer(int, yaml_representer)
yaml.add_representer(NoneType, null_representer)
