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

"""Automatic-calibration Node module, which works with notebooks as nodes."""

import json
import logging
import os
from datetime import datetime
from io import StringIO
from typing import Any

import numpy as np
import papermill as pm

from qililab.config import logger

logger_output_start = "RAND_INT:47102512880765720413 - OUTPUTS: "


class CalibrationNode:
    """Automatic calibration Node class representing a node in the calibration graph.

    The calibration graph represents a calibration procedure, where each node represents a step of this calibration procedure. **Each of these steps consists of:**

    - **A Jupyter Notebook** to calibrate or check the data with (including its metadata for execution time checks). Such a notebook should contain the following:

        **1) An input parameters cell** (tagged as `parameters`). These parameters are the ones to be overwritten by the ``input_parameters``.

        **2) An experiment/circuit** with its corresponding loops for the sweep given by ``sweep_interval``.

        **3) An analysis procedure**, that plots and fits the obtained data to the expected theoretical behavior, finding the optimal desired parameters.

        **4) An export data cell**, that calls ``export_nb_outputs()`` with the dictionary to retrieve data from the notebook into the calibration workflow.
        This dictionary contains a ``platform_parameters`` list of parameters to set on the platform and might also contain "fidelities", for the fidelities notebooks.

        .. note::

            More information about the notebooks contents and execution, can be found in the examples below.

    - **Inputs to pass to this notebook (optional)**, which might vary for different calls of the same notebook, such:
        ``sweep_interval``, ``input_parameters`` (kwargs).

    .. note::

        If the same notebook is going to be used multiple times for the same ``qubit``, then you need to pass a ``node_distinguisher`` argument, so the :class:`.CalibrationController`
        makes the graph mapping correctly.

    Args:
        nb_path (str): Full notebook path with the folder, nb_name, and ``.ipynb`` extension, written in unix format: `folder/subfolder/.../file.ipynb`.
        qubit_index (int | list[int], optional): Qubit on which this notebook will be executed. Defaults to None.
        node_distinguisher (int | str, optional): Distinguisher for when the same notebook its used multiple times in the same qubit. Mandatory to use in such case, or
            the :class:`.CalibrationController` won't do the graph mapping properly, and the calibration will fail. Defaults to None.
        input_parameters (dict, optional): Kwargs for input parameters to pass and be interpreted by the notebook. Defaults to None.
        sweep_interval (np.ndarray, optional): Array describing the sweep values of the experiment. Defaults to None, which means the one specified in the notebook will be used.

    |

    **Notebooks execution workflow:**

    First the key functionality of this class is implemented in the ``run_node()`` method**. The workflow of ``run_node()`` is as follows:

    1. Prepare any input parameters needed for the notebook, including extra parameters defined by the user and essential ones such as the targeted qubit or the sweep intervals.

    2. Create a file with a temporary name. This file will be used to save the execution of the notebook and initially has the following format:

        ``NameOfTheNode_TimeExecutionStarted_dirty.ipynb``

        The ``_dirty`` flag is added to identify executions that are not completed. Since the data we would find such file is ``dirty``, not completed.

    3. Start the execution of the notebook. There are three possible outcomes:

        3.1) The execution succeeds. If the execution succeeds, the execution file is renamed by updating the timestamp and removing the dirty flag:

            ``NameOfTheNode_TimeExecutionEnded.ipynb``

        3.2) The execution is interrupted. If the execution is interrupted, the ``_dirty`` flag remains in the filename, and the program exits:

            ``NameOfTheNode_TimeExecutionStarted_dirty.ipynb``

        3.2) An exception is thrown. This case is not controlled by the user like interruptions. Instead, exceptions are automatically thrown when
        an error is detected. When an execution error is found, the execution file is renamed with the time the error occurred, adding the `_error` flag, and the program exits:

            ``NameOfTheNode_TimeExecutionFoundError_error.ipynb``

        A more detailed explanation of the error is reported and also described inside the notebook (see `papermill documentation
        <https://papermill.readthedocs.io/en/latest/>`_ for more detailed information).

    At the end of this process, you obtain an executed and saved notebook for manual inspection, along with the optimal parameters to set in the runcard
    and the achieved fidelities.

    ----------

    Examples:

        To calibrate two linked experiments (first and second), for 2 distinct qubits:

        .. code-block:: python

            # qubit_0: first -> second
            #
            # qubit_1: first -> second

        you first need to create the 1Q nodes (and import the needed packages), and build the :class:`.CalibrationController` graph with which to calibrate them:

        .. code-block:: python

            import numpy as np
            import networkx as nx

            from qililab.calibration import CalibrationController, CalibrationNode, norm_root_mean_sqrt_error

            # GRAPH CREATION AND NODE MAPPING (key = name in graph, value = node object):
            nodes = {}
            G = nx.DiGraph()

            # CREATE NODES :
            for qubit in [0, 1]:
                first = CalibrationNode(
                    nb_path="notebooks/first.ipynb",
                    qubit_index=qubit,
                )
                nodes[first.node_id] = first

                second = CalibrationNode(
                    nb_path="notebooks/second.ipynb",
                    qubit_index=qubit,
                    sweep_interval=np.arange(start=0, stop=19, step=1),
                )
                nodes[second.node_id] = second

                # GRAPH BUILDING (1 --> 2):
                G.add_edge(first.node_id, second.node_id)

            # CREATE CALIBRATION CONTROLLER:
            controller = CalibrationController(node_sequence=nodes, calibration_graph=G, runcard=path_runcard)

            ### MAIN WORKFLOW TO DO:
            controller.run_automatic_calibration()  # calibrate all the nodes in the graph, starting from the roots until the leaves.

            ### OPTIONAL WORKFLOW TO DO:
            controller.calibrate_all(second)    # calibrate all the needed dependencies until you can calibrate the second node for qubit 1
                                                # and then calibrate it. Calibrating first and second for qubit 1, in this order.
        .. note::

            A more complex graph to calibrate is found in the :class:`CalibrationController` class documentation.

        |

        where **the notebooks ``first/second.ipynb``, would contain** the following:

        |

        **1) An input parameters cell** (tagged as `parameters`). These parameters are the ones to be overwritten by the ``input_parameters``:

            .. code-block:: python

                import numpy as np

                qubit = 0

                # Sweep interval:
                sweep_interval = np.arange(start=0, stop=19, step=1)

                # Extra parameters for this concrete notebook:
                param1 = 0
                param2 = 0
                ...

        |

        **2) An experiment/circuit** with its corresponding loops for the sweep given by ``sweep_interval``.

            .. code-block:: python

                # Set the environment and paths:
                ...

                # Set the platform:
                platform = ql.build_platform(path=platform_path)
                platform.connect()
                platform.initial_setup()
                platform.turn_on_instruments()

                # Define circuit
                circuit = ...

                # Loop over the sweeps executing the platform:
                results = []
                for X in sweep_interval:
                    platform.set_parameter(alias=alias, parameter=ql.Parameter.X, value=X)
                    result = platform.execute(program=circuit, num_avg=hw_avg, repetition_duration=repetition_duration)
                    results.append(result.array)

                results = np.hstack(results)

        |

        **3) An analysis procedure**, that plots and fits the obtained data to the expected theoretical behaviour and finds the optimal desired parameters.

            .. code-block:: python

                def fit(xdata, results): ...


                fitted_values, x_data, y_data, figure = fit(xdata=sweep_interval, results=results)
                plt.show()

        |

        **4) An export data cell**, that calls ``export_nb_outputs()`` with the dictionary to retrieve from the notebook into the calibration workflow:

            .. code-block:: python

                from qililab.calibration.calibration_node import export_nb_outputs

                export_nb_outputs(
                    {
                        "platform_parameters": [
                            (param_name0, fitted_values[0], bus_alias0, qubit),
                            (param_name1, fitted_values[1], bus_alias1, qubit),
                        ],
                        "fidelities": [
                            (qubit, "fidelity1", 0.9),
                            (qubit, "fidelity2", 0.95),
                        ],  # Fidelities in the output dictionary are optional.
                    }
                )

        where the ``platform_parameters`` are a list of parameters to set on the platform. And the ``fidelities`` are for showing results
        in the calibration report, or for using the checkpoints in the calibration with the ``checkpoint`` and ``check_value`` arguments.

        .. note::

            If more than one `export_nb_outputs()` is used in the notebook, only the last one will be collected.

    """

    def __init__(
        self,
        nb_path: str,
        qubit_index: int | list[int] | None = None,
        node_distinguisher: int | str | None = None,
        input_parameters: dict | None = None,
        sweep_interval: np.ndarray | None = None,
    ):
        if len(nb_path.split("\\")) > 1:
            raise ValueError("`nb_path` must be written in unix format: `folder/subfolder/.../file.ipynb`.")

        if isinstance(qubit_index, list) and len(qubit_index) != 2:
            raise ValueError("List of `qubit_index` only accepts two qubit index")

        self.nb_path: str = os.path.abspath(nb_path)
        """Absolute notebook path, with folder, nb_name and ``.ipynb`` extension."""

        self.qubit_index: int | list[int] | None = qubit_index
        """Qubit which this notebook will be executed on."""

        self.node_distinguisher: int | str | None = node_distinguisher
        """Distinguisher for when the same notebook its used multiple times in the same qubit. Mandatory to use in such case, or
        the :class:`.CalibrationController` won't do the graph mapping properly, and the calibration will fail. Defaults to None.
        """

        self.node_id, self.nb_folder = self._path_to_name_and_folder(self.nb_path)
        """Node name and folder, separated, and without the ``.ipynb`` extension."""

        self.input_parameters: dict | None = input_parameters
        """Kwargs for input parameters, to pass and then be interpreted by the notebook. Defaults to None."""

        self.sweep_interval: np.ndarray | None = sweep_interval
        """Array describing the sweep values of the experiment. Defaults to None, which means the one specified in the notebook will be used."""

        self.output_parameters: dict | None = None
        """Output parameters dictionary from the notebook execution, which was extracted with ``ql.export_nb_outputs()``, normally contains
        a ``platform_parameters`` which will be the calibrated parameters to set in the platform and might also contain "fidelities", for
        the fidelities notebooks. If no previous successful calibration, then is None.
        """

        self.previous_timestamp: float | None = self.get_last_calibrated_timestamp()
        """Last calibrated timestamp. If no previous successful calibration, then is None."""

        self._stream: StringIO = self._build_notebooks_logger_stream()
        """Stream object to which the notebooks logger output will be written, to posterior retrieval."""

        self.been_calibrated: bool = False
        """Flag whether this notebook has been already calibrated in a concrete run. Defaults to False."""

    def run_node(self) -> float:
        """Executes the notebook, passing the needed parameters and flags.

        **Its workflow is the following:**

        1. Prepare any input parameters needed for the notebook. This includes extra parameters defined by the user and essential ones such as the targeted qubit or the sweep intervals.

        2. Create a file with a temporary name. This file will be used to save the execution of the notebook, and at this stage has the following format:

            ``NameOfTheNode_TimeExecutionStarted_dirty.ipynb``

            The "_dirty" flag is added to the execution files in order to identify the executions that are not completed. So we know that the data we find
            if we open that file is "dirty", not completed.

        3. Start execution of the notebook. From where we can expect 3 possible outcomes from the execution:

            3.1) The execution succeds. If the execution succeds, we rename the execution file by updating the timestamp and removing the dirty flag:

                ``NameOfTheNode_TimeExecutionEnded.ipynb``

            3.2) The execution is interrupted. If the execution is interrupted, the "_dirty" flag will remain in the filename for ever. Notice after an
            interruption the program exits.

                ``NameOfTheNode_TimeExecutionStarted_dirty.ipynb``

            3.2) An exception is thrown. This case is not controlled by the user like the interruptions, instead those exceptions are automatically
            thrown when an error is detected. When an execution error is found, the execution file is renamed with the time that the error ocurred and adding the flag "_error":

                ``NameOfTheNode_TimeExecutionFoundError_error.ipynb``

            A more detailed explanation of the error is reported and also described inside the notebook (see `papermill documentation
            <https://papermill.readthedocs.io/en/latest/>`_ for more detailed information).Then after we post-processed the file, the program exits.

        at the end, from all of this, you will obtain, a executed and saved notebook to manually check, and an outputs dictionary, containing the optimal
        parameters to set in the runcard, together with the achieved fidelities.

        Returns:
            float: Timestamp to identify the notebook execution moment.

        Exits:
            In case of a keyboard interruption or any exception during the execution of the notebook.
        """
        # Create the input parameters for the notebook:)
        params: dict = {}

        if isinstance(self.qubit_index, int):
            params |= {"qubit": self.qubit_index}
        elif isinstance(self.qubit_index, list):
            params |= {"control_qubit": self.qubit_index[0], "target_qubit": self.qubit_index[1]}

        if self.sweep_interval is not None:
            params["sweep_interval"] = self.sweep_interval

        if self.input_parameters is not None:
            params |= self.input_parameters

        # JSON serialize nb input, no np.ndarrays
        params = _json_serialize(params)

        # initially the file is "dirty" until we make sure the execution was not aborted, so we add _dirty tag.
        output_path = self._create_notebook_datetime_path(dirty=True)

        # Execute notebook without problems:
        try:
            self.output_parameters = self._execute_notebook(self.nb_path, output_path, params)
            timestamp = datetime.timestamp(datetime.now())
            # remove the _dirty tag, since it finished.
            new_output_path = self._create_notebook_datetime_path(timestamp=timestamp)
            os.rename(output_path, new_output_path)
            return timestamp

        # When keyboard interrupt (Ctrl+C), generate error, and leave `_dirty` in the name:
        except KeyboardInterrupt as exc:  # we don't remove the _dirty tag, since it was stopped, not failed.
            logger.error("Interrupted automatic calibration notebook execution of %s", self.nb_path)
            raise KeyboardInterrupt(f"Interrupted automatic calibration notebook execution of {self.nb_path}") from exc

        # When notebook execution fails, generate error folder and move there the notebook:
        except Exception as exc:
            if output_path in [entry.path for entry in os.scandir(os.getcwd())]:
                timestamp = datetime.timestamp(datetime.now())
                error_path = self._create_notebook_datetime_path(
                    timestamp=timestamp, error=True
                )  # add _error tag, for failed executions.
                os.rename(output_path, error_path)
                logger.error(
                    "Aborting execution. Exception %s during automatic calibration notebook execution, trace of the error can be found in %s",
                    str(exc),
                    error_path,
                )

                raise Exception(
                    f"Aborting execution. Exception {exc!s} during automatic calibration notebook execution, trace of the error can be found in {error_path}"
                ) from exc

            logger.error(
                "Aborting execution. Exception %s during automatic calibration, expected error execution file to be created but it did not",
                str(exc),
            )

            raise Exception(
                f"Aborting execution. Exception {exc!s} during automatic calibration, expected error execution file to be created but it did not"
            ) from exc

    @staticmethod
    def _build_notebooks_logger_stream() -> StringIO:
        """Build a stream object for capturing the notebook's log output.

        Returns:
            StringIO: Stream object for capturing execution outputs.
        """
        stream = StringIO()
        logging.basicConfig(stream=stream, level=logging.INFO)

        return stream

    def _execute_notebook(self, input_path: str, output_path: str, parameters: dict | None = None) -> dict | None:
        """Executes a Jupyter Notebook overwriting the `parameters` cell, and capturing the execution ``output``.

        This method changes the working directory to the notebook folder before executing the notebook and restores the original working directory after execution if necessary.

        Args:
            input_path (str): The input path of the notebook to be executed.
            output_path (str): The output path where the executed noteboo will be saved. If None, no file will be saved.
            parameters (dict, optional): Input parameters kwargs, to overwrite the notebook `parameters` cell with. Defaults to None.

        Returns:
            dict | None: A dictionary containing the output parameters of the execution.

        Raises:
            IncorrectCalibrationOutput: In case no outputs or multiple outputs where found.
        """
        # Save previous working directory and setup notebook folder as working directory
        original_wd = os.getcwd()
        os.chdir(self.nb_folder)
        pm.execute_notebook(input_path, output_path, parameters, log_output=True, stdout_file=self._stream)
        # Restore previous working directory after execution is done
        os.chdir(original_wd)

        # Retrieve the logger info and extract the output from it:
        logger_string = self._stream.getvalue()
        return self._from_logger_string_to_output_dict(logger_string, input_path)

    def _create_notebook_datetime_path(
        self, timestamp: float | None = None, dirty: bool = False, error: bool = False
    ) -> str:
        """Create a timestamped notebook path, adding the datetime to the file name end, just before the ``.ipynb``.

        If the path directory doesn't exist, it gets created.

        The passed path can have the ``.ipynb`` extension or not.

        The part of the string after the last "/" will be considered the file name, and the part before its directory.

        Args:
            original_path (str): The original path of the notebook, to add the datetime to. The path directory doesn't need to exist. Can have the ``.ipynb`` extension or not.
                The part of the string after the last "/" will be considered the file name, and the part before it's directory.
            timestamp (float, optional): Timestamp to add to the name. If None, the current time will be used. Defaults to None.
            dirty (bool, optional): Flag indicating if the notebook is in a "dirty" state. Defaults to False.
            error (bool, optional): Flag indicating if the notebook comes from an execution error. Defaults to False.

        Returns:
            str: The timestamped notebook absolute path.
        """
        # Create datetime pathHM
        now = datetime.now() if timestamp is None else datetime.fromtimestamp(timestamp)
        daily_path = f"{now.year}_{now.month:02d}_{now.day:02d}"
        now_path = f"{daily_path}-" + f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"

        # If doesn't exist, create the needed folder for the path
        os.makedirs(self.nb_folder, exist_ok=True)

        # Path of the execution
        flag = "_error" if error else ("_dirty" if dirty else "")

        # Return the string where saved
        return f"{self.nb_folder}/{self.node_id}_{now_path}{flag}.ipynb"

    def _path_to_name_and_folder(self, original_path: str) -> tuple[str, str]:
        """Extract the name and folder from a notebook path. Name will be extended with the qubit it acts on.

        The passed path can have the ``.ipynb`` extension or not.

        The part of the string after the last "/" will be considered the file name, and the part before its directory.

        Args:
            original_path (str): The original path of the notebook. Can have the ``.ipynb`` extension or not.
                The part of the string after the last "/" will be considered the file name, and the part before it's directory.

        Returns:
            tuple[str, str]: A tuple containing the notebook name and its folder.
        """
        # Create qubit_string to add:
        qubit_str = (
            f"_q{self.qubit_index!s}"
            if isinstance(self.qubit_index, int)
            else "_" + "".join(f"q{q}" for q in self.qubit_index)
            if isinstance(self.qubit_index, list)
            else ""
        )

        # Create distinguish_string to differentiate multiple calls of the same node:
        distinguish_str = f"_{self.node_distinguisher!s}" if self.node_distinguisher is not None else ""

        # Remove .ipynb from end if it has one, and separate the folder and name with the last "/":
        split_path = original_path.split(".ipynb")[0].split("/")

        name = split_path.pop() + distinguish_str + qubit_str
        folder_path = "/".join(split_path)
        return name, folder_path

    def get_last_calibrated_timestamp(self) -> float | None:
        """Gets the timestamp of the last successful calibration of the notebook.

        Searches the directory for self.node_id+“_calibrated” and gets the latest creation time.

        Returns:
            float | None: The timestamp of the last successful calibration, or None if no calibration has been completed.
        """
        last_modified_file_name = self._find_last_executed_calibration()
        return (
            os.path.getmtime(os.path.join(self.nb_folder, last_modified_file_name))
            if last_modified_file_name is not None
            else None
        )

    def _find_last_executed_calibration(self) -> str | None:
        """Finds the last executed calibration of the node.

        Returns:
            str | None: The path of the last calibrated notebook, or None if none has been executed.
        """
        # Filtering by node_id and calibrations
        file_names = [
            entry.name
            for entry in os.scandir(self.nb_folder)
            if entry.is_file()
            and f"{self.node_id}" in entry.name
            and "_calibrated" in entry.name.split(f"{self.node_id}")[1]
        ]
        # Get the last created file, most recent one
        return (
            max(file_names, key=lambda fname: os.path.getctime(os.path.join(self.nb_folder, fname)))
            if file_names != []
            else None
        )

    def _from_logger_string_to_output_dict(self, logger_string: str, input_path: str) -> dict | None:
        """Returns the output dictionary from a logger output string. Raises errors if the output doesn't follow the expected format.

        Args:
            logger_string (str): The logger string containing the output dictionary to extract.
            input_path (str): Path of the notebook that generated the output, to raise errors.

        Returns:
            dict | None: The output dictionary of the file execution.

        Raises:
            IncorrectCalibrationOutput: In case multiple outputs where found.
        """
        logger_splitted = logger_string.split(logger_output_start)
        # In case no output is found we return None:
        if len(logger_splitted) < 2:
            return None
        # In case more than one output is found, we keep the last one, and raise a warning:
        if len(logger_splitted) > 2:
            logger.warning("If you had multiple outputs exported in %s, the last one found will be used.", input_path)

        # This next line is for taking into account other encodings, where special characters get `\\` in front.
        clean_data = logger_splitted[-1].split("\\n")[0].replace('\\"', '"')

        logger_outputs_string = clean_data.split("/n")[0].split("\n")[0]  # Remove the last \n for both bars directions
        return json.loads(logger_outputs_string)  # in-dictionary strings will need to be double-quoted "" not ''.

    def _add_string_to_checked_nb_name(self, string_to_add: str, timestamp: float) -> None:
        """Adds a string to the checked notebook name.

        Args:
            string_to_add (str): The string to append to the notebook name.
            timestamp (float): The timestamp to use for the new notebook execution name.
        """
        timestamp_path = self._create_notebook_datetime_path(timestamp=timestamp).split(".ipynb")[0]

        os.rename(f"{timestamp_path}.ipynb", f"{timestamp_path}_{string_to_add}.ipynb")


def export_nb_outputs(outputs: dict) -> None:
    """Function to export notebook outputs into a stream, later collected by the :class:`CalibrationNode` class.

    If this function is used more than once in a notebook, only the last one will be collected.

    Args:
        outputs (dict): Outputs from the notebook to export into the automatic calibration workflow.
    """
    outputs = _json_serialize(outputs)
    print(f"{logger_output_start}{json.dumps(outputs)}")  # noqa: T201


def _json_serialize(obj: Any):
    """Function to JSON serialize the input argument.

    Needed to handle input/output of notebook executions from the :class:`CalibrationNode` class.
    This method only looks for np.ndarrays objects to JSON serialize. Any other non-JSON serializable won't be serialized.

    Args:
        obj (Any): Object to serialize
    """
    if isinstance(obj, (list, tuple, np.ndarray)):
        return [_json_serialize(elem) for elem in obj]

    if isinstance(obj, dict):
        return {_json_serialize(k): _json_serialize(v) for k, v in obj.items()}

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return float(obj)

    if isinstance(obj, (complex, np.complex128, np.complex64, np.complex128)):
        return {"real": float(obj.real), "imag": float(obj.imag)}

    if isinstance(obj, np.bool_):
        return bool(obj)

    if isinstance(obj, np.void):
        return None

    return obj
