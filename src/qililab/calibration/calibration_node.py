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
from typing import Callable

import numpy as np
import papermill as pm

from qililab.config import logger

logger_output_start = "RAND_INT:47102512880765720413 - OUTPUTS: "


class CalibrationNode:  # pylint: disable=too-many-instance-attributes
    """Automatic-calibration Node class, which represent a node in the calibration graph.

    The calibration graph represents a calibration procedure, so each node represent a step of this calibration procedure. **Each of these steps consists of:**

    - **A Jupyter Notebook** to calibrate or check the data with (and its metadata to do execution times checks). Such notebook would contain the following:

        **1) An input parameters cell** (tagged as `parameters`). These parameters are the ones to be overwritten by the ``input_parameters``:

        **2) An experiment/circuit** with its corresponding loops for the sweep given by ``sweep_interval``.

        **3) An analysis procedure**, that plots and fits the obtained data to the expected theoretical behaviour and finds the optimal desired parameters.

        **4) An export data cell**, that calls ``export_calibration_outputs()`` with the dictionary to retrieve from the notebook into the calibration workflow.
        Such dictionary contains a ``check_parameters`` dictionary of the obtained results to do comparisons against, and a ``platform_params`` list of
        parameters to set on the platform.

        .. note::

            More information about the notebook contents can be found in the examples below.

    - **Thresholds and Models for the Comparisons** of data, and metadata, of this notebook. Arguments on this category:
        ``in_spec_threshold``, ``bad_data_threshold``, ``comparison_model``, ``drift_timeout``

    - **Inputs to pass to this notebook (optional)**, which might vary for different calls of the same notebook. Arguments on this category:
        ``sweep_interval``, ``number_of_random_datapoints``, ``input_parameters`` (kwargs)

    --------------------------------

    |

    **The execution of a notebook is the key functionality of this class,** this is implemented in the ``run_node()`` method, whose workflow is the following:

    1. Prepare any input parameters needed for the notebook. This includes extra parameters defined by the user and essential ones such as the targeted qubit or the sweep intervals.

    2. Create a file with a temporary name. This file will be used to save the execution of the notebook, and at this stage has the following format:

        ``NameOfTheNode_TimeExecutionStarted_dirty.ipynb``

        The "_dirty" flag is added to the execution files in order to identify the executions that are not completed. So we know that the data we find if we
        open that file is "dirty", not completed.

    3. Start execution of the notebook. From where we can expect 3 possible outcomes from the execution:

        3.1) The execution succeds. If the execution succeds, we rename the execution file by updating the timestamp and removing the dirty flag:

            ``NameOfTheNode_TimeExecutionEnded.ipynb``

        3.2) The execution is interrupted. If the execution is interrupted, the "_dirty" flag will remain in the filename for ever. Notice after an interruption
        the program exits.

            ``NameOfTheNode_TimeExecutionStarted_dirty.ipynb``

        3.2) An exception is thrown. This case is not controlled by the user like the interruptions, instead those exceptions are automatically thrown when
        an error is detected. When an execution error is found, the execution file is moved to a new subfolder ``/error_executions`` and renamed with the
        time that the error ocurred and adding the flag "_error":

            ``NameOfTheNode_TimeExecutionFoundError_error.ipynb``

        A more detailed explanation of the error is reported and also described inside the notebook (see `papermill documentation
        <https://papermill.readthedocs.io/en/latest/>`_ for more detailed information). Then after we post-processed the file, the program exits.

    at the end, from all of this, you will obtain, a executed and saved notebook to manually check, and the optimal parameters to set in the runcard,
    together with the  achieved fidelities.

    |

    Args:
        nb_path (str): Full notebook path, with folder, nb_name and ``.ipynb`` extension. The path should be written in unix format: `folder/subfolder/.../file.ipynb`.
        in_spec_threshold (float): Threshold such that the ``check_data()`` methods return `in_spec` or `out_of_spec`.
        bad_data_threshold (float): Threshold such that the ``check_data()`` methods return `out_of_spec` or `bad_data`.
        comparison_model (Callable): Comparison model used, to compare data in this node.
        drift_timeout (float): A durations in seconds, representing an estimate of how long it takes for the parameter to drift. During that time the parameters of
            this node should be considered calibrated, without the need to check the data.
        input_parameters (dict | None, optional): Kwargs for input parameters, to pass and then be interpreted by the notebook. Defaults to None.
        sweep_interval (np.ndarray | None, optional): Array describing the sweep values of the experiment. Defaults to None, which means the one specified in the notebook will be used.
        number_of_random_datapoints (int, optional): The number of points, chosen randomly within the sweep interval, to check with ``check_data()`` if the experiment
            gets the same outcome as during the last calibration that was run. Default value is 10.

    Examples:

        In this example, you will create 2 linked nodes twice, one for each qubit, and pass them to a :class:`.CalibrationController`:

        .. code-block:: python

            import numpy as np
            sweep_interval = np.arange(start=0, stop=19, step=1)

            # GRAPH CREATION AND NODE MAPPING (key = name in graph, value = node object):
            nodes = {}
            G = nx.DiGraph()

            # CREATE NODES :
            for qubit in [0, 1]:
                first = CalibrationNode(
                    nb_path="notebooks/first.ipynb",
                    qubit_index=qubit,
                    in_spec_threshold=4,
                    bad_data_threshold=8,
                    comparison_model=norm_root_mean_sqrt_error,
                    drift_timeout=1800.0,
                )
                nodes[first.node_id] = first

                second = CalibrationNode(
                    nb_path="notebooks/second.ipynb",
                    qubit_index=qubit,
                    in_spec_threshold=2,
                    bad_data_threshold=4,
                    comparison_model=norm_root_mean_sqrt_error,
                    drift_timeout=1.0,
                    sweep_interval=sweep_interval,
                )
                nodes[second.node_id] = second

                # GRAPH BUILDING (1 --> 2):
                G.add_edge(first.node_id, second.node_id)

            # CREATE CALIBRATION CONTROLLER:
            controller = CalibrationController(node_sequence=nodes, calibration_graph=G, runcard=path_runcard)

        |

        where the notebook ``example.ipynb``, would contain the following:

            **1) An input parameters cell** (tagged as `parameters`). These parameters are the ones to be overwritten by the ``input_parameters``:

            .. code-block:: python

                import numpy as np

                # ``check_data()`` parameters:
                check = False
                number_of_random_datapoints = 10
                qubit=0

                # Sweep interval:
                sweep_interval = np.arange(start=0, stop=19, step=1)

                # Extra parameters for this concrete notebook:
                param1=0
                param2=0
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
                results_list = []
                for X in sweep_interval:
                    platform.set_parameter(alias=alias, parameter=ql.Parameter.X, value=X)
                    result = platform.execute(program=circuit, num_avg=hw_avg, repetition_duration=repetition_duration)
                    results_list.append(result.array)

                results = np.hstack(results_list)

            |

            **3) An analysis procedure**, that plots and fits the obtained data to the expected theoretical behaviour and finds the optimal desired parameters.

            .. code-block:: python

                def fit(xdata, results):
                    ...

                fitted_values, x_data, y_data, figure = fit(xdata=sweep_interval, results=results)
                plt.show()

            |

            **4) An export data cell**, that calls ``export_calibration_outputs()`` with the dictionary to retrieve from the notebook into the calibration workflow:

            .. code-block:: python

                from qililab.automatic_calibration.calibration_node import export_calibration_outputs

                export_calibration_outputs(
                    {
                        "check_parameters": {"x": sweep_interval, "y": results},
                        "platform_params": [(bus_alias0, qubit, param_name0, fitted_values[0]), (bus_alias1, qubit, param_name1, fitted_values[1])],
                        "fidelities": [(qubit, "fidelity1", 0.9), (qubit, "fidelity2", 0.95)]  # Fidelities in the output dictionary are optional.
                    }
                )

            where the ``check_parameters`` are a dictionary of the saved results to do comparisons against. And the ``platform_params`` are a list of parameters to set on the platform.
    """

    def __init__(
        self,
        nb_path: str,
        in_spec_threshold: float,
        bad_data_threshold: float,
        comparison_model: Callable,
        drift_timeout: float,
        qubit_index: int | list[int] | None = None,
        input_parameters: dict | None = None,
        sweep_interval: np.ndarray | None = None,
        number_of_random_datapoints: int = 10,
    ):
        if in_spec_threshold > bad_data_threshold:
            raise ValueError("`in_spec_threshold` must be smaller or equal than `bad_data_threshold`.")

        if len(nb_path.split("\\")) > 1:
            raise ValueError("`nb_path` must be written in unix format: `folder/subfolder/.../file.ipynb`.")

        self.nb_path: str = nb_path
        """Full notebook path, with folder, nb_name and ``.ipynb`` extension."""

        self.qubit_index: int | list[int] | None = qubit_index
        """Qubit which this notebook will be executed on."""

        self.node_id, self.nb_folder = self._path_to_name_and_folder(nb_path)
        """Node name and folder, separated, and without the ``.ipynb`` extension."""

        self.in_spec_threshold: float = in_spec_threshold
        """Threshold such that the ``check_data()`` methods return `in_spec` or `out_of_spec`."""

        self.bad_data_threshold: float = bad_data_threshold
        """Threshold such that the ``check_data()`` methods return `out_of_spec` or `bad_data`."""

        self.comparison_model: Callable = comparison_model
        """Comparison model used, to compare data in this node."""

        self.drift_timeout: float = drift_timeout
        """A durations in seconds, representing an estimate of how long it takes for the parameter to drift. During that time the parameters of
        this node should be considered calibrated, without the need to check the data.
        """

        self.input_parameters: dict | None = input_parameters
        """Kwargs for input parameters, to pass and then be interpreted by the notebook. Defaults to None."""

        self.sweep_interval: np.ndarray | None = sweep_interval
        """Array describing the sweep values of the experiment. Defaults to None, which means the one specified in the notebook will be used."""

        self.number_of_random_datapoints: int = number_of_random_datapoints
        """The number of points, chosen randomly within the sweep interval, to check with ``check_data()`` if the experiment
        gets the same outcome as during the last calibration that was run. Default value is 10.
        """

        self.output_parameters: dict | None = self.get_last_calibrated_output_parameters()
        """Output parameters dictionary from the notebook execution, which was extracted with ``ql.export_calibration_outputs()``, normally contains
        a ``check_params`` to do the ``check_data()`` and the ``platform_params`` which will be the calibrated parameters to set in the platform.

        If no previous successful calibration, then is None.
        """

        self.previous_output_parameters: dict | None = None
        """Same output_parameters, but from the previous execution of the Node. Starts at None."""

        self.previous_timestamp: float | None = self.get_last_calibrated_timestamp()
        """Last calibrated timestamp. If no previous successful calibration, then is None."""

        self._stream: StringIO = self._build_notebooks_logger_stream()
        """Stream object to which the notebooks logger output will be written, to posterior retrieval."""

    def run_node(self, check: bool = False) -> float:
        """Executes the notebook, passing the needed parameters and flags. Also it can be chosen to only check certain values of the sweep interval for
        when checking data.

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
            thrown when an error is detected. When an execution error is found, the execution file is moved to a new subfolder ``/error_executions``
            and renamed with the time that the error ocurred and adding the flag "_error":

                ``NameOfTheNode_TimeExecutionFoundError_error.ipynb``

            A more detailed explanation of the error is reported and also described inside the notebook (see `papermill documentation
            <https://papermill.readthedocs.io/en/latest/>`_ for more detailed information).Then after we post-processed the file, the program exits.

        at the end, from all of this, you will obtain, a executed and saved notebook to manually check, and an outputs dictionary, containing the optimal
        parameters to set in the runcard, together with the achieved fidelities, and the data for future comparisons.

        Args:
            check (bool, optional): Flag to make a ``check_data()`` instead than a normal ``calibrate()`` with the notebook. Defaults to ``False`` (normal calibrate).

        Returns:
            float: Timestamp to identify the notebook execution.

        Exits:
            In case of a keyboard interruption or any exception during the execution of the notebook.
        """
        # Create the input parameters for the notebook:)
        params: dict = {
            "check": check,
            "number_of_random_datapoints": self.number_of_random_datapoints,
            "qubit": self.qubit_index,
        }

        if self.sweep_interval is not None:
            params["sweep_interval"] = self._build_check_data_interval() if check else self.sweep_interval

        if self.input_parameters is not None:
            params |= self.input_parameters

        # initially the file is "dirty" until we make sure the execution was not aborted
        output_path = self._create_notebook_datetime_path(self.nb_path, dirty=True)
        self.previous_output_parameters = self.output_parameters

        # Execute notebook without problems:
        try:
            self.output_parameters = self._execute_notebook(self.nb_path, output_path, params)

            timestamp = datetime.timestamp(datetime.now())
            new_output_path = self._create_notebook_datetime_path(self.nb_path, timestamp)
            os.rename(output_path, new_output_path)
            return timestamp

        # When keyboard interrupt (Ctrl+C), generate error, and leave `_dirty`` in the name:
        except KeyboardInterrupt as exc:
            logger.error("Interrupted automatic calibration notebook execution of %s", self.nb_path)
            raise KeyboardInterrupt(f"Interrupted automatic calibration notebook execution of {self.nb_path}") from exc

        # When notebook execution fails, generate error folder and move there the notebook:
        except Exception as exc:  # pylint: disable = broad-exception-caught
            timestamp = datetime.timestamp(datetime.now())
            error_path = self._create_notebook_datetime_path(self.nb_path, timestamp, error=True)
            os.rename(output_path, error_path)
            logger.error(
                "Aborting execution. Exception %s during automatic calibration notebook execution, trace of the error can be found in %s",
                str(exc),
                error_path,
            )
            # pylint: disable = broad-exception-raised
            raise Exception(
                f"Aborting execution. Exception {str(exc)} during automatic calibration notebook execution, trace of the error can be found in {error_path}"
            ) from exc

    @staticmethod
    def _build_notebooks_logger_stream() -> StringIO:
        """Build the stream object to save the logger outputs of the notebooks:

        Returns:
            StringIO: stream object where all the notebook outputs are saved and retrieved from.
        """
        stream = StringIO()
        logging.basicConfig(stream=stream, level=logging.INFO)

        return stream

    def _execute_notebook(self, input_path: str, output_path: str, parameters: dict | None = None) -> dict:
        """Executes python notebooks overwriting the parameters of the `parameters` cells and then returns the ``output`` parameters of such notebook.

        Args
            input_path (str): Path to input notebook to execute.
            output_path (str): Path to save executed notebook. If None, no file will be saved.
            parameters (dict): Arbitrary keyword arguments to pass to the notebook parameters. It will overwrite the `parameters` cell of the notebook.

        Returns:
            dict: Kwargs for the output parameters of the notebook.

        Raises:
            IncorrectCalibrationOutput: In case no outputs, incorrect outputs or multiple outputs where found. Incorrect outputs are those that do not contain `check_parameters` or is empty.
        """
        pm.execute_notebook(input_path, output_path, parameters, log_output=True, stdout_file=self._stream)

        # Retrieve the logger info and extract the output from it:
        logger_string = self._stream.getvalue()
        return self._from_logger_string_to_output_dict(logger_string, input_path)

    def _build_check_data_interval(self) -> np.ndarray | None:
        """Build ``check_data()`` sweep interval with ``number_of_random_datapoints`` data points.

        Returns:
            list: ``check_data()`` sweep interval list.
        """
        if (interval := self.sweep_interval) is not None:
            return np.array(
                [int(interval[np.random.randint(0, len(interval))]) for _ in range(self.number_of_random_datapoints)]
            )
        return None

    def _create_notebook_datetime_path(
        self, original_path: str, timestamp: float | None = None, dirty: bool = False, error: bool = False
    ) -> str:
        """Adds the datetime to the file name end, just before the ``.ipynb``.

        If the path directory doesn't exist, it gets created.

        The passed path can have the ``.ipynb`` extension or not.

        The part of the string after the last "/" will be considered the file name, and the part before its directory.

        Args:
            original_path (str): The original path to add the datetime to. The path directory doesn't need to exist. Can have the ``.ipynb`` extension or not.
                The part of the string after the last "/" will be considered the file name, and the part before it's directory.
            timestamp (float): Timestamp to add to the name. If None, datetime.now() will be used. Defaults to None.

        Returns:
            str: new notebook path with the timestamp in it.
        """
        # Create datetime pathHM
        now = datetime.now() if timestamp is None else datetime.fromtimestamp(timestamp)
        daily_path = f"{now.year}_{now.month:02d}_{now.day:02d}"
        now_path = f"{daily_path}-" + f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"

        # If doesn't exist, create the needed folder for the path
        name, folder_path = self._path_to_name_and_folder(original_path)
        os.makedirs(folder_path, exist_ok=True)

        if dirty and not error:  # return the path of the execution
            return f"{folder_path}/{name}_{now_path}_dirty.ipynb"
        if error:
            os.makedirs(f"{folder_path}/error_executions", exist_ok=True)
            return f"{folder_path}/error_executions/{name}_{now_path}_error.ipynb"

        # return the string where saved
        return f"{folder_path}/{name}_{now_path}.ipynb"

    def _path_to_name_and_folder(self, original_path: str) -> tuple[str, str]:
        """Transforms a path into name and folder. Name will be extended with the qubit it acts on.

        The passed path can have the ``.ipynb`` extension or not.

        The part of the string after the last "/" will be considered the file name, and the part before its directory.

        Args
            original_path (str): The original path to add the datetime to. Can have the ``.ipynb`` extension or not.
                The part of the string after the last "/" will be considered the file name, and the part before it's directory.

        Returns:
            tuple[str, str]: Node name and folder, separated, and without the ``.ipynb`` extension.
        """
        # Create qubit_string to add:
        qubit_str = (
            f"_q{str(self.qubit_index)}"
            if isinstance(self.qubit_index, int)
            else "_" + "".join(f"q{q}" for q in self.qubit_index)
            if isinstance(self.qubit_index, list)
            else ""
        )

        # Remove .ipynb from end if it has one, and separate the folder and name with the last "/":
        path_list = original_path.split(".ipynb")[0].split("/")

        name = path_list.pop() + qubit_str
        folder_path = "/".join(path_list)
        return name, folder_path

    def get_last_calibrated_timestamp(self) -> float | None:
        """Gets the last calibration timestamp if there exist any previous execution of the same notebook.

        Searches the directory for self.node_id+“_calibrated” and gets the latest creation time.

        Returns:
            float: The last execution timestamp if exists, None otherwise.
        """
        last_modified_file_name = self._find_last_executed_calibration()
        return (
            os.path.getmtime(os.path.join(self.nb_folder, last_modified_file_name))
            if last_modified_file_name is not None
            else None
        )

    def get_last_calibrated_output_parameters(self) -> dict | None:
        """Gets the last output of the previous calibration execution of the same notebook if there exist any.

        Searches the directory for self.node_id+“_calibrated” and gets the outputs from the latest creation time one.

        Returns:
            dict: The last calibration execution output if exists, None otherwise.
        """
        last_modified_file_name = self._find_last_executed_calibration()
        return (
            self._parse_output_from_execution_file(last_modified_file_name)
            if last_modified_file_name is not None
            else None
        )

    def _find_last_executed_calibration(self) -> str | None:
        """Returns the filename of the last calibration execution with the same node_id.

        Returns:
            str: Name of the file.
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

    def _parse_output_from_execution_file(self, file_name) -> dict | None:
        """Parses a expected notebook file and gets the output from the execution converted as python dictionary.

        Args:
            file_name (str): filename of the notebook file.

        Returns:
            dict: outputs of the executed notebook file.

        Raises:
            IncorrectCalibrationOutput: In case no outputs, incorrect outputs or multiple outputs where found. Incorrect outputs are those that do not contain `check_parameters` or is empty.
        """
        # Parsing file
        outputs_lines: list[str] = []
        try:
            with open(os.path.join(self.nb_folder, file_name), encoding="utf-8") as file:
                lines = file.readlines()
                outputs_lines.extend(line for line in lines if line.find(logger_output_start) != -1)
        except Exception as exc:
            logger.error("No previous execution found of notebook %s.", self.nb_path)
            raise FileNotFoundError(f"No previous execution found of notebook {self.nb_path}.") from exc

        # Check how many lines contain an output, to raise the corresponding errors:
        if len(outputs_lines) != 1:
            logger.error("No output or various outputs found in notebook %s.", self.nb_path)
            raise IncorrectCalibrationOutput(f"No output or various outputs found in notebook {self.nb_path}.")

        # When only one line of outputs, use that one:
        return self._from_logger_string_to_output_dict(outputs_lines[0], self.nb_path)

    def _from_logger_string_to_output_dict(self, logger_string, input_path):
        """Returns the output dictionary from the logger string, or raises errors if ``logger_string`` doesn't follow the expected format.

        Args
            logger_string (str): The logger string containing the output dictionary to extract.
            input_path (str): Path of the notebook that generated the output, to raise errors.

        Returns:
            dict: Kwargs for the output parameters of the notebook.

        Raises:
            IncorrectCalibrationOutput: In case no outputs, incorrect outputs or multiple outputs where found. Incorrect outputs are those that do not contain `check_parameters` or is empty.
        """
        logger_splitted = logger_string.split(logger_output_start)

        # In case something unexpected happened with the output we raise an error
        if len(logger_splitted) != 2:
            logger.error("No output or various outputs found in notebook %s.", input_path)
            raise IncorrectCalibrationOutput(f"No output or various outputs found in notebook {input_path}.")

        # This next line is for taking into account other encodings, where special characters get `\\` in front.
        clean_data = logger_splitted[1].split("\\n")[0].replace('\\"', '"')

        logger_outputs_string = clean_data.split("\n")[0]
        out_dict = json.loads(logger_outputs_string)

        if "check_parameters" not in out_dict or out_dict["check_parameters"] == {}:
            logger.error(
                "Aborting execution. No 'check_parameters' dictionary or its empty in the output cell implemented in %s",
                input_path,
            )
            raise IncorrectCalibrationOutput(
                f"Empty output found in {input_path}, output must have key and value 'check_parameters'."
            )
        return out_dict

    def _add_string_to_checked_nb_name(self, string_to_add: str, timestamp: float) -> None:
        """Adds a string to the notebook name and returns it.

        Args:
            string_to_add (str): The string to add in the end of the name.
            timestamp (float): Timestamp to identify the desired notebook execution.
        """
        path = os.path.join(self.nb_folder, self.node_id)
        timestamp_path = self._create_notebook_datetime_path(path, timestamp).split(".ipynb")[0]

        os.rename(f"{timestamp_path}.ipynb", f"{timestamp_path}_{string_to_add}.ipynb")

    def _invert_output_and_previous_output(self) -> None:
        """Reverts the output and previous output, for when we run notebook in a ``check_data()``."""
        self.output_parameters, self.previous_output_parameters = (
            self.previous_output_parameters,
            self.output_parameters,
        )


def export_calibration_outputs(outputs: dict) -> None:
    """Function to export notebook outputs into a stream, later collected by the :class:`CalibrationNode` class.

    Args:
        outputs (dict): Outputs from the notebook to export into the automatic calibration workflow.
    """
    print(f"{logger_output_start}{json.dumps(outputs)}")


class IncorrectCalibrationOutput(Exception):
    """Error raised when the output of a calibration node is incorrect."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"IncorrectCalibrationOutput: {self.message}"
