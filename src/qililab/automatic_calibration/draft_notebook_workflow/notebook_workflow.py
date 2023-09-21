"""Notebook WorkFLow class example"""
import json
import logging
import os
from datetime import datetime
from io import StringIO

import papermill as pm


class NbWorkFlow:
    """Notebook workflow class, it creates the stream object and passes it to the notebook executions."""

    def __init__(self):
        self.stream = self.build_notebooks_logger_stream()

    @staticmethod
    def build_notebooks_logger_stream() -> StringIO:
        """Build the stream object to save the logger outputs of the notebooks:

        Returns:
            StringIO: stream object where all the notebook outputs are saved and retrived from.
        """
        stream = StringIO()
        logging.basicConfig(stream=stream, level=logging.INFO)

        return stream

    def execute_notebook(self, input_path: str, output_path: str, parameters: dict | None = None) -> dict:
        """Executes python notebooks overwritting the parameters of the "parameters" cells and then returns the `output` parameters of such notebook.

        Args
            input_path (str): Path to input notebook or NotebookNode object of notebook
            output_path (str): Path to save executed notebook. If None, no file will be saved
            parameters (dict): Arbitrary keyword arguments to pass to the notebook parameters. It will overwrite the "parameters" cell of the notebook.
            stream (StringIO): Stream object where all the notebook outputs are saved and retrived from.

        Returns:
            dict: Kwargs for the output parameters of the notebook.
        """
        # Execute the notebook with the passed parameters, and getting the log output:
        pm.execute_notebook(input_path, output_path, parameters, log_output=True)

        # Retrieve the logger info and extract the output from it:
        logger_string = self.stream.getvalue()
        logger_output_string = logger_string.split("OUTPUTS: ")[-1].split("\n")[0]

        return json.loads(logger_output_string)

    @staticmethod
    def create_notebook_datetime_path(original_path: str) -> str:
        """Adds the datetime to the file name end, just before the ``.ipynb``.

        If the path directory doesn't exist, it gets created.

        The passed path can have the ``.ipynb`` extension or not.

        The part of the string after the last "/" will be considered the file name, and the part before its directory.

        Args:
            original_path (str): The original path to add the datetime to. The path directory doesn't need to exist. Can have the ``.ipynb`` extension or not.
                The part of the string after the last "/" will be considered the file name, and the part before it's directory.
        """
        # Create datetime pathH
        now = datetime.now()
        daily_path = f"{now.year}_{now.month:02d}_{now.day:02d}"
        now_path = f"{daily_path}-" + f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"

        # Remove .ipynb from end if it has:
        shorted_path = original_path.split(".ipynb")[0]

        # If doesn't exist, create the needed folder for the path (remove anything after the last "/"):
        folder_path_list = shorted_path.split("/")
        folder_path_list.pop()
        folder_path = "/".join(folder_path_list)
        os.makedirs(folder_path, exist_ok=True)

        # return the string where saved
        return f"{shorted_path}_{now_path}.ipynb"
