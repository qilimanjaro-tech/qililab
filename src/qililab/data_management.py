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

import os
import shutil
import tempfile
from enum import Enum
from pathlib import Path

from ruamel.yaml import YAML

from .platform import Platform
from .settings import Runcard


def _represent_enum(representer, data):
    """Serialise any ``Enum`` member as its underlying value (e.g. a plain string).

    Several ``set_parameter`` implementations store ``str, Enum`` members (``ReferenceClock``,
    ``VNASweepTypes``, ``SourceMode``, ``IntegrationMode``, ...) directly into the settings.
    ruamel.yaml cannot represent those Enum members, which made ``save_platform`` raise a
    ``RepresenterError``. Coercing to ``data.value`` dumps the same plain value that a runcard
    loaded from disk would hold, so the save round-trips.
    """
    return representer.represent_data(data.value)


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

    # Resolve symlinks so that, when `new_path` points at a symlinked runcard, we write through
    # to (and atomically replace) the real file instead of replacing the link with a plain file.
    target = Path(os.path.realpath(new_path))

    data = platform.to_dict()
    yaml = YAML()
    # Make the dumper coerce any Enum member (that a `set_parameter` may have stored in the
    # settings) to its underlying value, so serialisation never fails with a RepresenterError.
    yaml.representer.add_multi_representer(Enum, _represent_enum)

    # Serialise atomically: dump to a temporary file in the same directory and only then replace
    # the target with os.replace. If anything above fails, the temporary file is removed and the
    # existing runcard at `target` is left untouched, instead of being truncated to 0 bytes by
    # opening the target in write mode.
    fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    replaced = False
    try:
        with os.fdopen(fd, mode="w", encoding="utf-8") as file:
            yaml.dump(data=data, stream=file)
        if target.exists():
            # Preserve the permissions of the runcard being overwritten; mkstemp creates the
            # temporary file with owner-only 0o600, which brand-new runcards keep.
            shutil.copymode(target, tmp_name)
        os.replace(tmp_name, target)
        replaced = True
    finally:
        if not replaced and os.path.exists(tmp_name):
            os.unlink(tmp_name)

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
