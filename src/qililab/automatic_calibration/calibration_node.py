"""Automatic-calibration Node module, which works with notebooks as nodes."""
import json
import logging
import os
from datetime import datetime
from io import StringIO

import papermill as pm

from qililab.automatic_calibration.calibration_utils import get_timestamp


class CalibrationNode:
    """Automatic-calibration Node class, which works with notebooks as nodes.

    Args:
        nb_path (str): Full notebook path, with folder, nb_name and ``.ipynb`` extension.
        in_spec_threshold (float): Threshold such that the ``check_data()`` methods return `in_spec` or `out_of_spec`.
        bad_data_threshold (float): Threshold such that the ``check_data()`` methods return `out_of_spec` or `bad_data`.
        drift_timeout (float): Time for which we believe the parameters of this node should still be considered calibrated, without checking the data.
        input_parameters (dict | None): Extra input parameters to pass to the notebook, a part than the ``sweep_interval`` and the ``number_of_random_datapoints``. Defaults to None.
        sweep_interval (dict | None): Sweep interval to pass to the notebook. If not specified, the default one written in the notebook will be used. Defaults to None.
        number_of_random_datapoints (int): Random number of points to do the ``check_data()``. Defaults to 10.
    """

    def __init__(
        self,
        nb_path: str,
        in_spec_threshold: float,
        bad_data_threshold: float,
        drift_timeout: float,
        input_parameters: dict | None = None,
        sweep_interval: dict | None = None,
        number_of_random_datapoints: int = 10,
    ):
        self.nb_path: str = nb_path
        """Full notebook path, with folder, nb_name and ``.ipynb`` extension"""

        self.node_id, self.nb_folder = self.path_to_name_and_folder(nb_path)
        """Node name and folder, separated, and without the ``.ipynb`` extension"""

        self.in_spec_threshold = in_spec_threshold
        """Threshold such that the ``check_data()`` methods return `in_spec` or `out_of_spec`."""

        self.bad_data_threshold = bad_data_threshold
        """Threshold such that the ``check_data()`` methods return `out_of_spec` or `bad_data`."""

        self.drift_timeout: float = drift_timeout
        """Time for which we believe the parameters of this node should still be considered calibrated, without checking the data."""

        self.input_parameters: dict | None = input_parameters
        """Extra input parameters to pass to the notebook, a part than the ``sweep_interval`` and the ``number_of_random_datapoints``."""

        self.sweep_interval: dict | None = sweep_interval
        """Sweep interval to pass to the notebook. If not specified, the default one written in the notebook will be used."""

        self.number_of_random_datapoints: int = number_of_random_datapoints
        """Random number of points to do the ``check_data()``."""

        self.output_parameters: dict | None = None
        """Output parameters dictionary from the notebook execution, which get extracted with ``ql.export_calibration_putputs()``, normally contains
        a ``check_params`` to do the ``check_data()`` and the ``platform_params`` which will be the calibrated parameters to set in the platform. """

        self.previous_output_parameters: dict | None = None
        """Same output_parameters, but from the previous excecution of the Node."""

        self.previous_timestamp: float | None = self._get_last_calibrated_timestamp()
        """Last calibrated timestamp."""

        self.stream = self.build_notebooks_logger_stream()
        """Stream object to which the notbooks logger output will be written, to posterior retrieval."""

    def add_string_to_checked_nb_name(self, string_to_add: str, timestamp: float) -> None:
        """Adds a string to the notebook name and returns it.

        Args:
            string_to_add (str): The string to add in the end of the name.
            timestamp (float): Timestamp to identify the desired notebook excecution.
        """
        path = f"{self.nb_folder}/{self.node_id}"
        timestamp_path = self.create_notebook_datetime_path(path, timestamp).split(".ipynb")[0]

        os.rename(f"{timestamp_path}.ipynb", f"{timestamp_path}_{string_to_add}.ipynb")

    def run_notebook(self, check: bool = False) -> float:
        """Runs notebook with the parameters and paths of the Node. Also can be chosen to only check.

        Args:
            check (bool): Flag to make a ``calibrate()`` or a ``check_data()`` in the notebook.

        Returns:
            float: Timestamp to identify the notebook excecution.
        """
        params = {"check": check} | {"number_of_random_datapoints": self.number_of_random_datapoints}

        if self.sweep_interval is not None:
            params |= {
                "start": self.sweep_interval["start"],
                "end": self.sweep_interval["end"],
                "step": self.sweep_interval["step"],
            }

        if self.input_parameters is not None:
            params |= self.input_parameters

        output_path = self.create_notebook_datetime_path(self.nb_path)
        self.previous_output_parameters = self.output_parameters
        self.output_parameters = self._execute_notebook(self.nb_path, output_path, params)

        timestamp = get_timestamp()
        os.rename(output_path, self.create_notebook_datetime_path(self.nb_path, timestamp))
        return timestamp

    @staticmethod
    def build_notebooks_logger_stream() -> StringIO:
        """Build the stream object to save the logger outputs of the notebooks:

        Returns:
            StringIO: stream object where all the notebook outputs are saved and retrived from.
        """
        stream = StringIO()
        logging.basicConfig(stream=stream, level=logging.INFO)

        return stream

    def _execute_notebook(self, input_path: str, output_path: str, parameters: dict | None = None) -> dict:
        """Executes python notebooks overwritting the parameters of the "parameters" cells and then returns the `output` parameters of such notebook.

        Args
            input_path (str): Path to input notebook or NotebookNode object of notebook
            output_path (str): Path to save executed notebook. If None, no file will be saved
            parameters (dict): Arbitrary keyword arguments to pass to the notebook parameters. It will overwrite the "parameters" cell of the notebook.

        Returns:
            dict: Kwargs for the output parameters of the notebook.
        """
        # Execute the notebook with the passed parameters, and getting the log output:
        pm.execute_notebook(input_path, output_path, parameters, log_output=True, stdout_file=self.stream)

        # Retrieve the logger info and extract the output from it:
        logger_string = self.stream.getvalue()
        logger_outputs_string = logger_string.split("RAND_INT:47102512880765720413 - OUTPUTS: ")[-1].split("\n")[0]

        return json.loads(logger_outputs_string)

    def _get_last_calibrated_timestamp(self) -> float | None:
        """Gets the last executed timestamp if there exist any previous execution of the same notebook

        Returns:
            float: The last execution timestamp if exists, None otherwise.
        """
        # get all elems in that folder starting with self.node_id+"_" and get the last modiffied one file name, convert string into datetime
        entries = os.scandir(self.nb_folder)
        file_names = []
        for val in entries:
            if val.is_file():
                same_node_fnames = val.name.split(f"{self.node_id}_")
                if len(same_node_fnames) == 2 and len(val.name.split("_calibrated")) == 2:
                    file_names.append(val.name)

        last_modified_file_time = -1.0
        for fname in file_names:
            ftime = os.path.getmtime(f"{self.nb_folder}/{fname}")
            if ftime > last_modified_file_time:
                last_modified_file_time = ftime

        return last_modified_file_time if last_modified_file_time != -1.0 else None

    @classmethod
    def create_notebook_datetime_path(cls, original_path: str, timestamp: float | None = None) -> str:
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
        name, folder_path = cls.path_to_name_and_folder(original_path)
        os.makedirs(folder_path, exist_ok=True)

        # return the string where saved
        return f"{folder_path}/{name}_{now_path}.ipynb"

    @staticmethod
    def path_to_name_and_folder(original_path: str) -> tuple[str, str]:
        """Transforms a path into name and folder.

        The passed path can have the ``.ipynb`` extension or not.

        The part of the string after the last "/" will be considered the file name, and the part before its directory.

        Args:
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


def export_calibration_outputs(outputs: dict):
    """Function to export node outputs."""
    print(f"RAND_INT:47102512880765720413 - OUTPUTS: {json.dumps(outputs)}")
