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
from datetime import datetime
from pathlib import Path
from warnings import warn

import h5py
import numpy as np
from qiboconnection.api import API
from ruamel.yaml import YAML

from .platform import Platform
from .settings import Runcard


def save_results(results: np.ndarray, loops: dict[str, np.ndarray], data_path: str, name: str | None = None) -> str:
    """Save the given results and the platform.

    A timestamp is used to create a folder to save the data. The data will be saved within the file located in:
    ``path/yearmonthday/hourminutesecond_name/results.h5``.

    Args:
        results (np.ndarray): Array containing the results to be saved.
        loops (dict): A dictionary containing all the loops used in an experiment. The keys are used to identify the
            loop and the values of the dictionary correspond to the values of the loop.
        data_path (str): Path to the main data directory.
        name (str | None, optional): Name of the experiment. If given, the name is added to the name of the folder.
            Defaults to None.

    Returns:
        str: Path to folder where the results are saved.

    Examples:
        Imagine you want to run the following sequence:

        .. code-block:: python3

            circuit = Circuit(1)
            circuit.add(gates.X(0))
            circuit.add(gates.M(0))

            results_list = []
            gain_values = np.arange(0, 1, step=0.01)
            for gain in gain_values:
                platform.set_parameter(alias="drive_q0", parameter=ql.Parameter.GAIN, value=gain)
                result = platform.execute(circuit, num_avg=1000, repetition_duration=200000)
                results.append(result)

            results = np.hstack(results_list)

        You can then save the results by running:

        .. code-block:: python3

            loops = {"drive_q0_gain": gain_values}
            ql.save_results(results=results, loops=loops, path="data/", name="rabi")

        Imagine we call the cell above on August 22nd of 2023, at 15:14:12. The file will then be saved
        to: ``data/20230822/151412_rabi/results.h5``.
    """
    now = datetime.now()

    # Generate path to the daily folder
    daily_path = Path(data_path) / f"{now.year}{now.month:02d}{now.day:02d}"

    # Check if folder exists, if not create one
    if not os.path.exists(daily_path):
        os.makedirs(daily_path)

    # Generate path to the results folder
    now_path = str(daily_path / f"{now.hour:02d}{now.minute:02d}{now.second:02d}")

    if name is not None:
        now_path = f"{now_path}_{name}"

    # Check if folder exists, if not create one
    if not os.path.exists(now_path):
        os.makedirs(now_path)

    # Create or open an HDF5 file
    with h5py.File(f"{now_path}/results.h5", "w") as hf:
        # Save loops
        g = hf.create_group(name="loops")
        for loop_name, array in loops.items():
            g.create_dataset(name=loop_name, data=array)
        # Save results
        hf.create_dataset("results", data=results)

    return now_path


def load_results(path: str) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Load results from the given path to an `.h5` file.

    This function returns a tuple containing the array with the results, and a dictionary containing the loops of
    the experiment.

    Args:
        path (str): Path to the `.h5` file that needs to be loaded.

    Returns:
        tuple[np.ndarray, dict[str, np.ndarray]]: Tuple containing a numpy array with the saved results and a
        dictionary containing the loops of the experiment: ``{"loop_1": loop_1_values, "loop_2": loop_2_values, ...}``.

    Examples:
        Imagine you want to load the results of an experiment located in ``data/20230514/083005/results.h5``:

        >>> results, loops = ql.load_results(path="data/20230514/083005/results.h5")
        >>> results.shape
        (2, 50)
        >>> loops
        {'gain_drive_q0': array([0.  , 0.02, 0.04, 0.06, 0.08, 0.1 , 0.12, 0.14, 0.16, 0.18, 0.2 ,
                0.22, 0.24, 0.26, 0.28, 0.3 , 0.32, 0.34, 0.36, 0.38, 0.4 , 0.42,
                0.44, 0.46, 0.48, 0.5 , 0.52, 0.54, 0.56, 0.58, 0.6 , 0.62, 0.64,
                0.66, 0.68, 0.7 , 0.72, 0.74, 0.76, 0.78, 0.8 , 0.82, 0.84, 0.86,
                0.88, 0.9 , 0.92, 0.94, 0.96, 0.98])}
    """
    with h5py.File(path, "r") as hf:
        loops: dict[str, np.ndarray] = {name: data[:] for name, data in hf["loops"].items()}  # type: ignore
        results = hf["results"][:]  # type: ignore

    return results, loops  # type: ignore


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
    if not (path.endswith(".yml") or path.endswith(".yaml")):
        new_path = Path(path) / f"{platform.name}.yml"
    else:
        new_path = Path(path)

    with open(file=new_path, mode="w", encoding="utf-8") as file:
        YAML().dump(data=platform.to_dict(), stream=file)

    return str(new_path)


def build_platform(
    runcard: str | dict | None = None, path: str | None = None, connection: API | None = None, new_drivers: bool = False
) -> Platform:
    """Builds a :class:`.Platform` object, given a :ref:`runcard <runcards>`.

    Such runcard can be passed in one of the following two ways:
        - a path to a YAML file containing a dictionary of the serialized platform (runcard).
        - directly a dictionary of the serialized platform (runcard).

    |

    The dictionary should follow the next structure:

    .. code-block:: python3

        {
            "name": name,                                           # str
            "device_id": device_id,                                 # int
            "gates_settings": gates_settings,                       # dict
            "chip": chip,                                           # dict
            "buses": buses,                                         # list[dict]
            "instruments": instruments,                             # list[dict]
            "instrument_controllers": instrument_controllers        # list[dict]
        }

    which contains the information the :class:`.Platform` class uses to connect, setup and control the actual chip, buses and instruments of the laboratory.

    .. note::

        You can find more information about the complete structure of such dictionary, in the :ref:`Runcards <runcards>` section of the documentation.

    Args:
        path (str): Path to the platform's runcard YAML file. This argument is deprecated and will be removed soon.
        runcard (str | dict): Path to the platform's runcard YAML file, or direct dictionary of the platform's runcard info.
        connection (API | None, optional): Qiboconnection's API class used to block access to the Platform when connected to it.
            Defaults to None.
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
    if path is None and runcard is None:
        raise ValueError("`runcard` argument (str | dict) has not been passed to the `build_platform()` function.")
    if path is not None:
        if runcard is not None:
            raise ValueError("Use only the `runcard` argument, `path` argument is deprecated.")
        warn(
            "`path` argument is deprecated and will be removed soon. Use the `runcard` argument instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        runcard = path

    if new_drivers:
        raise NotImplementedError("New drivers are not supported yet.")

    if isinstance(runcard, str):
        with open(file=runcard, mode="r", encoding="utf8") as file:
            yaml = YAML(typ="safe")
            runcard = yaml.load(stream=file)

    runcard_class = Runcard(**runcard)
    return Platform(runcard=runcard_class, connection=connection)
