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
import sys
from datetime import datetime
from io import StringIO
from typing import Callable

import numpy as np
import papermill as pm

from qililab.config import logger

logger_output_start = "RAND_INT:47102512880765720413 - OUTPUTS: "


class CalibrationNode:  # pylint: disable=too-many-instance-attributes
    """Automatic-calibration Node class, which represent a node in the calibration graph.

    The calibration graph represents a calibration procedure, so each node represent a step of this calibration procedure.
    Each of these steps consists of:

    - **A Jupyter Notebook** to calibrate or check the data with (and its metadata to do execution times checks). Such notebook would contain the following:

        **1) An input parameters cell** (tagged as `parameters`). These parameters are the ones to be overwritten by the ``input_parameters``:

        **2) An experiment/circuit** with its corresponding loops for the sweep given by ``sweep_interval``.

        **3) An analysis procedure**, that plots and fits the obtained data to the expected theoretical behaviour and finds the optimal desired parameters.

        **4) An export data cell**, that calls ``export_calibration_outputs()`` with the dictionary to retrieve from the notebook into the calibration workflow.
        Such dictionary contains a ``check_parameters`` dictionary of the obtained results to do comparisons against, and a ``platform_params`` list of parameters to set on the platform.

        .. note::

            More information about the notebook contents can be found in the examples below.

    - **Thresholds and Models for the Comparisons** of data, and metadata, of this notebook. Arguments on this category:
        - ``in_spec_threshold``
        - ``bad_data_threshold``
        - ``comparison_model``
        - ``drift_timeout``

    - **Inputs to pass to this notebook (optional)**, which might vary for different calls of the same notebook. Arguments on this category:
        - ``sweep_interval`` (optional)
        - ``number_of_random_datapoints`` (optional)
        - ``input_parameters`` (optional kwargs, to be interpreted by the notebook)

    Args:
        nb_path (str): Full notebook path, with folder, nb_name and ``.ipynb`` extension.
        in_spec_threshold (float): Threshold such that the ``check_data()`` methods return `in_spec` or `out_of_spec`.
        bad_data_threshold (float): Threshold such that the ``check_data()`` methods return `out_of_spec` or `bad_data`.
        comparison_model (Callable): Comparison model used, to compare data in this node.
        drift_timeout (float): A durations in seconds, representing an estimate of how long it takes for the parameter to drift. During that time the parameters of
            this node should be considered calibrated, without the need to check the data.
        input_parameters (dict | None, optional): Kwargs for input parameters, to pass and then be interpreted by the notebook. Defaults to None.
        sweep_interval (dict | None, optional): Dictionary with 3 keys describing the sweep values of the experiment. The keys are: ``start``, ``stop`` and ``step``.
            The sweep values are all the numbers between 'start' and 'stop', separated from each other by the distance 'step'. Defaults to None, which means the one
            specified in the notebook will be used.
        number_of_random_datapoints (int, optional): The number of points, chosen randomly within the sweep interval, to check with ``check_data()`` if the experiment
            gets the same outcome as during the last calibration that was run. Default value is 10.

    Examples:

        In this example, you will create 2 nodes, and pass them to a :class:`.CalibrationController`:

        .. code-block:: python

            personalized_sweep_interval = {
                "start": 10,
                "stop": 50,
                "step": 2,
            }

            # CREATE NODES :
            first = CalibrationNode(
                nb_path="notebooks/example.ipynb",
                in_spec_threshold=4,
                bad_data_threshold=8,
                comparison_model=norm_root_mean_sqrt_error,
                drift_timeout=1800.0,
            )
            second = CalibrationNode(
                nb_path="notebooks/example.ipynb",
                in_spec_threshold=2,
                bad_data_threshold=4,
                comparison_model=norm_root_mean_sqrt_error,
                drift_timeout=1.0,
                sweep_interval=personalized_sweep_interval,
                number_of_random_datapoints=5,
            )

            # NODE MAPPING TO THE GRAPH (key = name in graph, value = node object):
            nodes = {"first": first, "second": second}

            # GRAPH CREATION:
            G = nx.DiGraph()
            G.add_edge("second", "first")

            # CREATE CALIBRATION CONTROLLER:
            controller = CalibrationController(node_sequence=nodes, calibration_graph=G, runcard=runcard_path)

        |

        where the notebook ``example.ipynb``, would contain the following:

            **1) An input parameters cell** (tagged as `parameters`). These parameters are the ones to be overwritten by the ``input_parameters``:

            .. code-block:: python

                # ``check_data()`` parameters:
                check = False
                number_of_random_datapoints = 10

                # Sweep interval:
                start = 0
                stop = 19
                step = 1

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
                        "platform_params": [(bus_alias0, param_name0, fitted_values[0]), (bus_alias1, param_name1, fitted_values[1])],
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
        input_parameters: dict | None = None,
        sweep_interval: dict | None = None,
        number_of_random_datapoints: int = 10,
    ):
        if in_spec_threshold > bad_data_threshold:
            raise ValueError("`in_spec_threshold` must be smaller or equal than `bad_data_threshold`.")

        self.nb_path: str = nb_path
        """Full notebook path, with folder, nb_name and ``.ipynb`` extension"""

        self.node_id, self.nb_folder = self._path_to_name_and_folder(nb_path)
        """Node name and folder, separated, and without the ``.ipynb`` extension"""

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

        self.sweep_interval: dict | None = sweep_interval
        """Dictionary with 3 keys describing the sweep values of the experiment. The keys are ``start``, ``stop`` and ``step``. The sweep values
        are all the numbers between ``start`` and ``stop``, separated from each other by the distance ``step``. Defaults to None, which means the one
        specified in the notebook will be used.
        """

        self.number_of_random_datapoints: int = number_of_random_datapoints
        """The number of points, chosen randomly within the sweep interval, to check with ``check_data()`` if the experiment
        gets the same outcome as during the last calibration that was run. Default value is 10.
        """

        self.output_parameters: dict | None = self._get_last_calibrated_output_parameters()
        """Output parameters dictionary from the notebook execution, which get extracted with ``ql.export_calibration_putputs()``, normally contains
        a ``check_params`` to do the ``check_data()`` and the ``platform_params`` which will be the calibrated parameters to set in the platform. """

        self.previous_output_parameters: dict | None = None
        """Same output_parameters, but from the previous execution of the Node."""

        self.previous_timestamp: float | None = self._get_last_calibrated_timestamp()
        """Last calibrated timestamp."""

        self.stream: StringIO = self._build_notebooks_logger_stream()
        """Stream object to which the notebooks logger output will be written, to posterior retrieval."""

    def _sweep_interval_as_array(self) -> list | None:
        """Transforms the sweep interval start, stop and step into a list.

        Returns:
            list: sweep interval list.
        """
        if self.sweep_interval is not None:
            return np.arange(
                self.sweep_interval["start"], self.sweep_interval["stop"], self.sweep_interval["step"]
            ).tolist()
        return None

    def _build_check_data_interval(self) -> list | None:
        """Build ``check_data()`` sweep interval with ``number_of_random_datapoints`` data points.

        Returns:
            list: ``check_data()`` sweep interval list.
        """
        if self.sweep_interval is not None:
            amp_values = np.arange(
                self.sweep_interval["start"], self.sweep_interval["stop"], self.sweep_interval["step"]
            )
            return [
                int(amp_values[np.random.randint(0, len(amp_values))]) for _ in range(self.number_of_random_datapoints)
            ]
        return None

    def add_string_to_checked_nb_name(self, string_to_add: str, timestamp: float) -> None:
        """Adds a string to the notebook name and returns it.

        Args:
            string_to_add (str): The string to add in the end of the name.
            timestamp (float): Timestamp to identify the desired notebook execution.
        """
        path = f"{self.nb_folder}/{self.node_id}"
        timestamp_path = self._create_notebook_datetime_path(path, timestamp).split(".ipynb")[0]

        os.rename(f"{timestamp_path}.ipynb", f"{timestamp_path}_{string_to_add}.ipynb")

    def run_notebook(self, check: bool = False) -> float | None:
        """Runs notebook with the parameters and paths of the Node. Also can be chosen to only check.

        Args:
            check (bool): Flag to make a ``calibrate()`` or a ``check_data()`` in the notebook.

        Returns:
            float: Timestamp to identify the notebook execution.
        """
        params: dict = {"check": check} | {"number_of_random_datapoints": self.number_of_random_datapoints}

        if self.sweep_interval is not None:
            params |= {
                "start": self.sweep_interval["start"],
                "stop": self.sweep_interval["stop"],
                "step": self.sweep_interval["step"],
            }
            if check:
                params |= {"sweep_interval": self._build_check_data_interval()}
            else:
                params |= {"sweep_interval": self._sweep_interval_as_array()}

        if self.input_parameters is not None:
            params |= self.input_parameters

        # initially the file is "dirty" until we make sure the execution was not aborted
        output_path = self._create_notebook_datetime_path(self.nb_path, dirty=True)
        self.previous_output_parameters = self.output_parameters

        try:
            self.output_parameters = self._execute_notebook(self.nb_path, output_path, params)
            print("Platform output parameters:", self.output_parameters["platform_params"])
            print("Check output parameters:", self.output_parameters["check_parameters"])
            if "fidelities" in self.output_parameters:
                print("Fidelities:", self.output_parameters["fidelities"])

            timestamp = self._get_timestamp()
            os.rename(output_path, self._create_notebook_datetime_path(self.nb_path, timestamp))
            return timestamp

        except KeyboardInterrupt:
            logger.info("Interrupted autocalibration notebook execution of %s", self.nb_path)
            return sys.exit()

        except Exception as e:  # pylint: disable = broad-exception-caught
            # Generate error folder and move there the notebook
            timestamp = self._get_timestamp()
            error_path = self._create_notebook_datetime_path(self.nb_path, timestamp, error=True)
            os.rename(output_path, error_path)
            logger.info(
                "Aborting execution. Exception %s during automatic calibration notebook execution, trace of the error can be found in %s",
                str(e),
                error_path,
            )
            return sys.exit()

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
        """Executes python notebooks overwriting the parameters of the "parameters" cells and then returns the `output` parameters of such notebook.

        Args
            input_path (str): Path to input notebook or NotebookNode object of notebook.
            output_path (str): Path to save executed notebook. If None, no file will be saved.
            parameters (dict): Arbitrary keyword arguments to pass to the notebook parameters. It will overwrite the "parameters" cell of the notebook.

        Returns:
            dict: Kwargs for the output parameters of the notebook.
        """
        pm.execute_notebook(input_path, output_path, parameters, log_output=True, stdout_file=self.stream)

        # Retrieve the logger info and extract the output from it:
        logger_string = self.stream.getvalue()
        logger_splitted = logger_string.split(logger_output_start)
        logger_outputs_string = logger_splitted[-1].split("\n")[0]

        # In case something unexpected happened with the output we raise an error
        if len(logger_splitted) < 2:
            logger.info(
                "Aborting execution. No output found, check the automatic-calibration output cell is implemented in %s",
                input_path,
            )
            raise IncorrectCalibrationOutput(f"No output found, check automatic-calibration notebook in {input_path}")
        if len(logger_splitted) > 2:
            logger.info(
                "Aborting execution. More than one output found, please output the results once in %s",
                input_path,
            )
            raise IncorrectCalibrationOutput(f"More than one output found in {input_path}")

        out_dict = json.loads(logger_outputs_string)

        if "check_parameters" not in out_dict or out_dict["check_parameters"] == {}:
            logger.info(
                "Aborting execution. No 'check_parameters' dictionary or its empty in the output cell implemented in %s",
                input_path,
            )
            raise IncorrectCalibrationOutput(
                f"Empty output found in {input_path}, output must have key and value 'check_parameters'."
            )
        return out_dict

    def _get_last_calibrated_timestamp(self) -> float | None:
        """Gets the last executed timestamp if there exist any previous execution of the same notebook.

        Returns:
            float: The last execution timestamp if exists, None otherwise.
        """
        # get all elems in that folder starting with self.node_id+“_” and get the last modiffied one file name, convert string into datetime
        last_modified_file_name = self._find_last_executed_calibration()
        return (
            os.path.getmtime(f"{self.nb_folder}/{last_modified_file_name}")
            if last_modified_file_name is not None
            else None
        )

    def _get_last_calibrated_output_parameters(self) -> dict | None:
        """Gets the last output of the previous calibration execution of the same notebook if there exist any.

        Returns:
            dict: The last calibration execution output if exists, None otherwise.
        """
        last_modified_file_name = self._find_last_executed_calibration()
        return (
            self._parse_output_from_execution_file(last_modified_file_name)
            if last_modified_file_name is not None
            else None
        )

    def _parse_output_from_execution_file(self, file_name) -> dict | None:
        """Parses a expected notebook file and gets the output from the execution converted as python dictionary.

        Args:
            file_name (str): filename of the notebook file.

        Returns:
            dict: outputs of the executed notebook file.
        """
        # Parsing file
        raw_string = ""
        with open(f"{self.nb_folder}/{file_name}") as file:  # pylint: disable=unspecified-encoding
            lines = file.readlines()
            start = False
            for line in lines:
                if line.find(logger_output_start) != -1:
                    raw_string += line
                    start = True
                if start and line.find("\n") == -1:
                    raw_string += line
                elif start:
                    raw_string += line
                    start = False

        # TODO: Make sure that the encoding of special characters (i.e. \\“) doesn’t depend on the OS because
        # Windows uses UTF-16LE and Linux (UNIX based like MacOS) uses UTF-8
        # Postprocessing file
        data = raw_string.split(logger_output_start)
        clean_data = data[1].split('\\n"')
        dict_as_string = clean_data[0].replace('\\"', '"')

        # converting list into one single string
        output_string = "".join(dict_as_string)
        return json.loads(output_string)

    def _find_last_executed_calibration(self) -> str | None:
        """Returns the filename of the last calibration execution with the same node_id.

        Returns:
            str: Name of the file.
        """
        # Filtering by node_id and calibrations
        entries = os.scandir(self.nb_folder)
        file_names = []
        for val in entries:
            if val.is_file():
                same_node_fnames = val.name.split(f"{self.node_id}_")
                if len(same_node_fnames) == 2 and len(val.name.split("_calibrated")) == 2:
                    file_names.append(val.name)

        # Get the last created file, most recent one
        last_modified_file_time, last_modified_file_name = -1.0, ""
        for fname in file_names:
            ftime = os.path.getctime(f"{self.nb_folder}/{fname}")
            if ftime > last_modified_file_time:
                last_modified_file_time, last_modified_file_name = ftime, fname

        return last_modified_file_name if last_modified_file_time != -1.0 else None

    @classmethod
    def _create_notebook_datetime_path(
        cls, original_path: str, timestamp: float | None = None, dirty: bool = False, error: bool = False
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
        name, folder_path = cls._path_to_name_and_folder(original_path)
        os.makedirs(folder_path, exist_ok=True)

        if dirty and not error:  # return the path of the execution
            return f"{folder_path}/{name}_{now_path}_dirty.ipynb"
        if error:
            os.makedirs(f"{folder_path}/error_executions", exist_ok=True)
            return f"{folder_path}/error_executions/{name}_{now_path}_error.ipynb"
        # return the string where saved
        return f"{folder_path}/{name}_{now_path}.ipynb"

    @staticmethod
    def _path_to_name_and_folder(original_path: str) -> tuple[str, str]:
        """Transforms a path into name and folder.

        The passed path can have the ``.ipynb`` extension or not.

        The part of the string after the last "/" will be considered the file name, and the part before its directory.

        Args
            original_path (str): The original path to add the datetime to. Can have the ``.ipynb`` extension or not.
                The part of the string after the last "/" will be considered the file name, and the part before it's directory.

        Returns:
            tuple[str, str]: Node name and folder, separated, and without the ``.ipynb`` extension.
        """
        # Remove .ipynb from end if it has:
        shorted_path = original_path.split(".ipynb")[0]

        # remove anything after the last "/":
        folder_path_list = shorted_path.split("/")
        name = folder_path_list.pop()
        folder_path = "/".join(folder_path_list)

        return name, folder_path

    def invert_output_and_previous_output(self) -> None:
        """Reverts the output and previous output, for when we run notebook in a ``check_data()``."""
        self.output_parameters, self.previous_output_parameters = (
            self.previous_output_parameters,
            self.output_parameters,
        )

    @staticmethod
    def _get_timestamp() -> float:
        """Generate a UNIX timestamp.

        Returns:
            float: UNIX timestamp of the time when the function is called.
        """
        now = datetime.now()
        return datetime.timestamp(now)


def export_calibration_outputs(outputs: dict) -> None:
    """Function to export notebook outputs into a stream, later collected by the CalibrationNode class.

    Args:
        outputs (dict): Outputs from the notebook to export into the CalibrationController/CalibrationNode workflow.
    """
    print(f"{logger_output_start}{json.dumps(outputs)}")


class IncorrectCalibrationOutput(Exception):
    """Error raised when the output of a calibration node is incorrect."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"IncorrectCalibrationOutput: {self.message}"
