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

from pathlib import Path

from ruamel.yaml import YAML

from .platform import Platform
from .settings import Runcard


def save_platform(path: str, platform: Platform) -> str:
    """Serialize and save the given platform to the specified path.

    This function saves the cache values of the :class:`.Platform` object during execution as a YAML file.
    It does not read the actual instruments. If you have previously used ``platform.set_parameter()`` without being
    connected to the instruments, it will save this "set" value as the cache values of the :class:`.Platform` object were modified.

    If the `path` string doesn't end with `.yml` or `.yaml`, this function assumes that `path` corresponds to an
    existing folder. The platform will then be saved inside the folder specified by `path` in a file called
    `platform_name.yml`, where `platform_name` corresponds to the `name` attribute of the given `Platform`.


    Args:
        path (str): Path to the folder/file where the YAML file will be saved.
        platform (Platform): Platform class to serialize and save to a YAML file.

    Returns:
        str: Path to the file where the platform is saved.

    Examples:
        If you save a platform by giving the path to a folder:

        >>> ql.save_platform(path="examples/runcards/", platform=platform)

        Qililab will use the name of the platform to create the YAML file. If ``platform.name == "galadriel"``, a file
        will be created in ``examples/runcards/galadriel.yml``.
    """
    if not (path.endswith((".yml", ".yaml"))):
        new_path = Path(path) / f"{platform.name}.yml"
    else:
        new_path = Path(path)

    with open(file=new_path, mode="w", encoding="utf-8") as file:
        YAML().dump(data=platform.to_dict(), stream=file)

    return str(new_path)


def build_platform(runcard: str | dict, new_drivers: bool = False) -> Platform:
    """Builds a :class:`.Platform` object, given a :ref:`runcard <runcards>`.

    Such runcard can be passed in one of the following two ways:
        - a path to a YAML file containing a dictionary of the serialized platform (runcard).
        - directly a dictionary of the serialized platform (runcard).

    |

    The dictionary should follow the next structure:

    .. code-block:: python3

        {
            "name": name,  # str
            "gates_settings": gates_settings,  # dict
            "chip": chip,  # dict
            "buses": buses,  # list[dict]
            "instruments": instruments,  # list[dict]
            "instrument_controllers": instrument_controllers,  # list[dict]
        }

    which contains the information the :class:`.Platform` class uses to connect, setup and control the actual chip, buses and instruments of the laboratory.

    .. note::

        You can find more information about the complete structure of such dictionary, in the :ref:`Runcards <runcards>` section of the documentation.

    Args:
        runcard (str | dict): Path to the platform's runcard YAML file, or direct dictionary of the platform's runcard info.
        new_drivers (bool, optional): Whether to use the new drivers or not. Defaults to False.

    Returns:
        Platform: Platform object.

    Examples:
        Passing the path of a YAML file containing a dictionary of the serialized platform, in the `runcard` argument:

        >>> platform = ql.build_platform(runcard="runcards/galadriel.yml")
        >>> platform.name
        galadriel

        Passing a dictionary of the serialized platform, in the `runcard` argument:

        >>> platform = ql.build_platform(runcard=galadriel_dict)
        >>> platform.name
        galadriel
    """
    if not isinstance(runcard, (str, dict)):
        raise ValueError(
            f"Incorrect type for `runcard` argument in `build_platform()`. Expected (str | dict), got: {type(runcard)}"
        )

    if new_drivers:
        raise NotImplementedError("New drivers are not supported yet.")

    if isinstance(runcard, str):
        with open(file=runcard, mode="r", encoding="utf8") as file:
            yaml = YAML(typ="safe")
            runcard = yaml.load(stream=file)

    runcard_class = Runcard(**runcard)  # type: ignore
    return Platform(runcard=runcard_class)
