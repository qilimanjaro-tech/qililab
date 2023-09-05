# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Yaml utils."""
import yaml


def yaml_representer(dumper: yaml.Dumper, value: int | float):
    """Int or float representer used by YAML."""
    tag = "int" if isinstance(value, int) else "float"
    text = f"{value:g}"
    if "e" in text:
        tag = "float"
        if "." not in text.split("e")[0]:
            # Add a decimal point if value is integer
            text = text.split("e")[0] + ".e" + "".join(text.split("e")[1:])
    if "." not in text and tag == "float":
        # Change tag to int if there is no decimal point.
        tag = "int"
    return dumper.represent_scalar(tag=f"tag:yaml.org,2002:{tag}", value=text)


def null_representer(dumper: yaml.Dumper, value: None):  # pylint: disable=unused-argument
    """Int or float representer used by YAML."""
    return dumper.represent_scalar(tag="tag:yaml.org,2002:null", value="")
