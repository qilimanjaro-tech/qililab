"""Test for the `CalibrationNode` class"""
import json
import logging
import os
from datetime import datetime
from io import StringIO
from typing import Callable
from unittest.mock import patch

import numpy as np
import papermill as pm
import pytest

from qililab.automatic_calibration.calibration_node import (
    CalibrationNode,
    IncorrectCalibrationOutput,
    export_calibration_outputs,
)
from qililab.config import logger

#################################################################################
#################################### SET UPS ####################################
#################################################################################

logger_output_start = "RAND_INT:47102512880765720413 - OUTPUTS: "


def dummy_comparison_model():
    pass


####################
### MOCKED NODES ###
####################
@pytest.fixture(name="public_methods_node")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_output_parameters")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_timestamp")
def fixture_public_methods_node(mocked_last_cal_params, mocked_last_cal_time) -> CalibrationNode:
    """Return a mocked CalibrationNode object."""
    return CalibrationNode(
        nb_path="./foobar.ipynb",
        in_spec_threshold=0.6,
        bad_data_threshold=0.9,
        comparison_model=dummy_comparison_model,
        drift_timeout=100,
    )


@pytest.fixture(name="private_methods_node")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_output_parameters")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_timestamp")
@patch("qililab.automatic_calibration.calibration_node.StringIO", autospec=True)
def fixture_private_methods_node(mocked_last_cal_params, mocked_last_cal_time, mocked_stringio) -> CalibrationNode:
    """Return a mocked CalibrationNode object.."""
    return CalibrationNode(
        nb_path="./foobar.ipynb",
        in_spec_threshold=0.6,
        bad_data_threshold=0.9,
        comparison_model=dummy_comparison_model,
        drift_timeout=100,
    )


@pytest.fixture(name="class_methods_node")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_output_parameters")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_timestamp")
def fixture_class_methods_node(mocked_last_cal_params, mocked_last_cal_time) -> CalibrationNode:
    """Return a mocked CalibrationNode object."""
    return CalibrationNode(
        nb_path="foo/bar.ipynb",
        in_spec_threshold=0.6,
        bad_data_threshold=0.9,
        comparison_model=dummy_comparison_model,
        drift_timeout=100,
    )


#################################################################################
############################## TESTS FOR THE CLASS ##############################
#################################################################################


###########################
### TEST INITIALIZATION ###
###########################
class TestInitializationCalibrationNode:
    """Unit tests for the CalibrationNode class initialization."""

    # TODO: Init test, mockear init fucntions calls and check their calls


class TestPublicMethodsFromCalibrationNode:
    """Unit tests for the CalibrationNode class public methods."""

    ##########################################
    ### TEST ADD STRING TO CHECKED NB NAME ###
    ##########################################
    def test_add_string_to_checked_nb_name(self, public_methods_node: CalibrationNode):
        """Test that ``add_string_to_checked_nb_name()`` works properly."""
        with patch("qililab.automatic_calibration.calibration_node.os.rename") as mocked_rename:
            path = f"{public_methods_node.nb_folder}/{public_methods_node.node_id}"
            timestamp_path = public_methods_node._create_notebook_datetime_path(path, 0).split(".ipynb")[0]
            string_to_add = "test_succesfull"
            public_methods_node.add_string_to_checked_nb_name(string_to_add, 0)
            mocked_rename.assert_called_once_with(f"{timestamp_path}.ipynb", f"{timestamp_path}_{string_to_add}.ipynb")

    #########################
    ### TEST RUN NOTEBOOK ###
    #########################
    # def test_run_notebook():
    """Test that run_notebook works properly."""
    #     #TODO: do all

    ##############################################
    ### TEST INVERT OUTPUT AND PREVIOUS OUTPUT ###
    ##############################################
    def test_invert_output_and_previous_output(self, public_methods_node: CalibrationNode):
        """Test that ``invert_output_and_previous_output()`` work properly."""
        test_output_params = {"test_output_params": "foo"}
        test_previous_output_params = {"test_previous_output_params": "bar"}
        public_methods_node.output_parameters, public_methods_node.previous_output_parameters = (
            test_output_params,
            test_previous_output_params,
        )
        public_methods_node.invert_output_and_previous_output()
        assert public_methods_node.output_parameters == test_previous_output_params
        assert public_methods_node.previous_output_parameters == test_output_params


class TestPrivateMethodsFromCalibrationNode:
    """Unit tests for the CalibrationNode class private methods."""

    ####################################
    ### TEST SWEEP INTERVAL AS ARRAY ###
    ####################################
    @pytest.mark.parametrize(
        "sweep_interval, expected",
        [(None, None), ({"start": 0, "stop": 5, "step": 1}, [0, 1, 2, 3, 4])],
    )
    def test_sweep_interval_as_array(self, private_methods_node: CalibrationNode, sweep_interval, expected):
        """Test that ``sweep_interval_as_array()`` works as expected."""
        private_methods_node.sweep_interval = sweep_interval
        test_value = private_methods_node._sweep_interval_as_array()
        assert test_value == expected

    ######################################
    ### TEST BUILD CHECK DATA INTERVAL ###
    ######################################
    @pytest.mark.parametrize(
        "sweep_interval, number_of_random_datapoints",
        [({"start": 0, "stop": 5, "step": 1}, 10), ({"start": 10, "stop": 1000, "step": 20}, 200)],
    )
    def test_build_check_data_interval(
        self, private_methods_node: CalibrationNode, sweep_interval, number_of_random_datapoints
    ):
        """Test that ``build_check_data_interval()`` works correctly."""
        private_methods_node.sweep_interval = sweep_interval
        private_methods_node.number_of_random_datapoints = number_of_random_datapoints
        sweep_interval_range = np.arange(sweep_interval["start"], sweep_interval["stop"], sweep_interval["step"])
        test_value = private_methods_node._build_check_data_interval()
        assert len(test_value) == private_methods_node.number_of_random_datapoints
        for value in test_value:
            assert value in sweep_interval_range

    #############################
    ### TEST EXECUTE NOTEBOOK ###
    #############################
    @patch("qililab.automatic_calibration.calibration_node.pm.execute_notebook")
    def test_execute_notebook(self, mocked_pm_exec, private_methods_node: CalibrationNode):
        """Testing general behavior of ``execute_notebook()``."""
        # Creating expected values for assert
        sweep_interval = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48]
        y = [i**2 for i in sweep_interval]
        results = {"x": sweep_interval, "y": y}
        expected = {"check_parameters": results, "platform_params": [["bus_alias", "param_name", 1]]}

        # Mocking return value of stream and calling execute_notebook
        raw_file_contents = 'RAND_INT:47102512880765720413 - OUTPUTS: {"check_parameters": {"x": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48], "y": [100, 144, 196, 256, 324, 400, 484, 576, 676, 784, 900, 1024, 1156, 1296, 1444, 1600, 1764, 1936, 2116, 2304]}, "platform_params": [["bus_alias", "param_name", 1]]}\n'
        private_methods_node.stream.getvalue.return_value = raw_file_contents  # type: ignore [attr-defined]
        test_value = private_methods_node._execute_notebook(private_methods_node.nb_path, "", {})

        # Asserts
        mocked_pm_exec.assert_called_once_with(
            private_methods_node.nb_path, "", {}, log_output=True, stdout_file=private_methods_node.stream
        )
        assert test_value == expected

    @pytest.mark.parametrize("output", ["", "a", "RAND_INT:4320765720413 - OUTPUTS: {'check_parameters': {'a':2}}/n"])
    @patch("qililab.automatic_calibration.calibration_node.pm.execute_notebook")
    @patch("qililab.automatic_calibration.calibration_node.logger", autospec=True)
    def test_execute_notebook_raises_no_output(self, mocked_logger, mocked_pm_exec, output, private_methods_node):
        """Testing when no outputs received from ``execute_notebook()``."""
        private_methods_node.stream.getvalue.return_value = output  # type: ignore [attr-defined]

        with pytest.raises(
            IncorrectCalibrationOutput,
            match=f"No output found, check automatic-calibration notebook in {private_methods_node.nb_path}",
        ):
            private_methods_node._execute_notebook(private_methods_node.nb_path, "", {})

        mocked_logger.info.assert_called_with(
            "Aborting execution. No output found, check the automatic-calibration output cell is implemented in %s",
            private_methods_node.nb_path,
        )

        mocked_pm_exec.assert_called_once_with(
            private_methods_node.nb_path, "", {}, log_output=True, stdout_file=private_methods_node.stream
        )

    @pytest.mark.parametrize(
        "output",
        [
            "RAND_INT:47102512880765720413 - OUTPUTS: {} RAND_INT:47102512880765720413 - OUTPUTS: {}",
            "RAND_INT:47102512880765720413 - OUTPUTS: {'check_parameters': {'a':2}}RAND_INT:47102512880765720413 - OUTPUTS: {'check_parameters': {'a':2}}/n",
        ],
    )
    @patch("qililab.automatic_calibration.calibration_node.pm.execute_notebook")
    @patch("qililab.automatic_calibration.calibration_node.logger", autospec=True)
    def test_execute_notebook_raises_more_than_one_output(
        self, mocked_logger, mocked_pm_exec, output, private_methods_node
    ):
        """Testing when more than one outputs are received from ``execute_notebook()`."""
        private_methods_node.stream.getvalue.return_value = output  # type: ignore [attr-defined]

        with pytest.raises(
            IncorrectCalibrationOutput,
            match=f"More than one output found in {private_methods_node.nb_path}",
        ):
            private_methods_node._execute_notebook(private_methods_node.nb_path, "", {})

        mocked_logger.info.assert_called_with(
            "Aborting execution. More than one output found, please output the results once in %s",
            private_methods_node.nb_path,
        )

        mocked_pm_exec.assert_called_once_with(
            private_methods_node.nb_path, "", {}, log_output=True, stdout_file=private_methods_node.stream
        )

    @pytest.mark.parametrize(
        "output",
        [
            "RAND_INT:47102512880765720413 - OUTPUTS: {}",
            'RAND_INT:47102512880765720413 - OUTPUTS: {"check_parameters":{}}',
        ],
    )
    @patch("qililab.automatic_calibration.calibration_node.pm.execute_notebook")
    @patch("qililab.automatic_calibration.calibration_node.logger", autospec=True)
    def test_execute_notebook_raises_empty_output(self, mocked_logger, mocked_pm_exec, output, private_methods_node):
        """Testing when outputs are empty received from ``execute_notebook()`."""
        private_methods_node.stream.getvalue.return_value = output  # type: ignore [attr-defined]

        with pytest.raises(
            IncorrectCalibrationOutput,
            match=f"Empty output found in {private_methods_node.nb_path}, output must have key and value 'check_parameters'.",
        ):
            private_methods_node._execute_notebook(private_methods_node.nb_path, "", {})

        mocked_logger.info.assert_called_with(
            "Aborting execution. No 'check_parameters' dictionary or its empty in the output cell implemented in %s",
            private_methods_node.nb_path,
        )

        mocked_pm_exec.assert_called_once_with(
            private_methods_node.nb_path, "", {}, log_output=True, stdout_file=private_methods_node.stream
        )

    #    def test_get_last_calibrated_timestamp():
    #        pass
    #
    #    def test_get_last_calibrated_output_parameters():
    #        pass

    #############################################
    ### TEST PARSE OUTPUT FROM EXECUTION FILE ###
    #############################################
    def test_parse_output_from_execution_file(self, private_methods_node: CalibrationNode):
        """Test that ``parse_output_from_execution_file`` works correctly."""
        # building a fixed dictionary for the test
        sweep_interval = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48]
        y = [i**2 for i in sweep_interval]
        results = {"x": sweep_interval, "y": y}
        expected_dict = {"check_parameters": results, "platform_params": [["bus_alias", "param_name", 1]]}

        # Dumping the raw string of the expected dictionary on a temporary file
        raw_file_contents = 'RAND_INT:47102512880765720413 - OUTPUTS: {"check_parameters": {"x": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48], "y": [100, 144, 196, 256, 324, 400, 484, 576, 676, 784, 900, 1024, 1156, 1296, 1444, 1600, 1764, 1936, 2116, 2304]}, "platform_params": [["bus_alias", "param_name", 1]]}\n'
        filename = "tmp_test_file.ipynb"
        with open(f"{private_methods_node.nb_folder}/{filename}", "w") as file:
            file.write(raw_file_contents)

        test_dict = private_methods_node._parse_output_from_execution_file(filename)
        assert test_dict == expected_dict
        os.remove(f"{private_methods_node.nb_folder}/{filename}")

    ###########################################
    ### TEST FIND LAST EXECUTED CALIBRATION ###
    ###########################################
    def test_find_last_executed_calibration(self, private_methods_node: CalibrationNode):
        """Test that ``find_last_executed_calibration()`` works correctly."""
        test_filenames = [
            "tmp_test_foobar_dirty.ipynb",
            "tmp_test_foobar_error.ipynb",
            "tmp_test_foo_calibrated.ipynb",
            "tmp_test_bar_calibrated.ipynb",
            "tmp_test_foobar_.ipynb",
        ]
        filename_expected = "tmp_test_foobar_calibrated.ipynb"

        for test_filename in test_filenames:
            f = open(f"{private_methods_node.nb_folder}/{test_filename}", "w")
            f.close()
        f = open(f"{private_methods_node.nb_folder}/{filename_expected}", "w")
        f.close()

        test_filename = private_methods_node._find_last_executed_calibration()

        assert filename_expected == test_filename

        for test_filename in test_filenames:
            os.remove(f"{private_methods_node.nb_folder}/{test_filename}")
        os.remove(f"{private_methods_node.nb_folder}/{filename_expected}")

    def test_find_last_executed_calibration_does_not_find_file(self, private_methods_node: CalibrationNode):
        # TODO: docstring, and check what do this test do, and if it makes sense?.
        test_filenames = [
            "tmp_test_foobar_dirty.ipynb",
            "tmp_test_foobar_error.ipynb",
            "tmp_test_foo_calibrated.ipynb",
            "tmp_test_bar_calibrated.ipynb",
            "tmp_test_foobar_.ipynb",
        ]

        for test_filename in test_filenames:
            f = open(f"{private_methods_node.nb_folder}/{test_filename}", "w")
            f.close()

        test_filename = private_methods_node._find_last_executed_calibration()

        assert test_filename is None

        for test_filename in test_filenames:
            os.remove(f"{private_methods_node.nb_folder}/{test_filename}")


class TestClassMethodsFromCalibrationNode:
    """Test the class methods of the `CalibrationNode`class."""

    ##########################################
    ### TEST CREATE NOTEBOOK DATETIME PATH ###
    ##########################################
    @pytest.mark.parametrize(
        "timestamp, dirty, error",
        [(None, True, True), (145783952598, False, True), (145783959532, False, False), (None, True, False)],
    )
    def test_create_notebook_datetime_path(
        self, timestamp, dirty, error, class_methods_node: CalibrationNode, original_path="foo/bar.ipynb"
    ):
        """Test ``that create_notebook_datetime_path()`` works correctly."""
        with patch("qililab.automatic_calibration.calibration_node.os") as mocked_os:
            test_value = class_methods_node._create_notebook_datetime_path(original_path, timestamp, dirty, error)
            mocked_os.makedirs.assert_called()
            if timestamp is not None:
                test_timestamp = datetime.fromtimestamp(timestamp)
                test_daily_path = f"{test_timestamp.year}_{test_timestamp.month:02d}_{test_timestamp.day:02d}"
                test_path = (
                    f"{test_daily_path}-"
                    + f"{test_timestamp.hour:02d}:{test_timestamp.minute:02d}:{test_timestamp.second:02d}"
                )

                assert f"_{test_path}" in test_value
            if dirty and not error:
                assert "foo/bar" in test_value
                assert "_dirty.ipynb" in test_value
            if error:
                mocked_os.makedirs.call_count == 2
                assert "foo/error_executions/bar" in test_value
                assert "_error.ipynb" in test_value


class TestStaticMethodsFromCalibrationNode:
    """Test static methods of the `CalibrationNode` class."""

    ##########################################
    ### TEST BUILD NOTEBOOKS LOGGER STREAM ###
    ##########################################
    @patch("qililab.automatic_calibration.calibration_node.logging", autospec=True)
    def test_build_notebooks_logger_stream(self, mocked_logging):
        """Test that ``build_notebooks_logger_stream()`` works properly."""
        stream = CalibrationNode._build_notebooks_logger_stream()
        mocked_logging.basicConfig.assert_called_once()
        assert isinstance(stream, StringIO)

    ####################################
    ### TEST PATH TO NAME AND FOLDER ###
    ####################################
    @pytest.mark.parametrize(
        "original_path, expected",
        [
            ("foo/bar/foobar.ipynb", ("foobar", "foo/bar")),
            ("this/is/a/long/path/to/notebook.ipynb", ("notebook", "this/is/a/long/path/to")),
        ],
    )
    def test_path_to_name_and_folder(self, original_path, expected):
        """Test that ``path_to_name_and_folder()`` works properly."""
        test_values = CalibrationNode._path_to_name_and_folder(original_path)
        assert len(test_values) == 2
        assert test_values[0] == expected[0]
        assert test_values[1] == expected[1]

    ###########################
    ### TEST GET TIMESTAMPS ###
    ###########################
    @patch("qililab.automatic_calibration.calibration_node.datetime", autospec=True)
    def test_get_timestamp(self, modked_datetime):
        """Test that ``get_timestamp()`` works properly."""
        CalibrationNode._get_timestamp()
        modked_datetime.now.assert_called_once()
        modked_datetime.timestamp.assert_called_once()


#################################################################################
######################## TESTS FOR THE EXTERNAL FUNCTIONS #######################
#################################################################################


#######################################
### TEST EXPORT CALIBRATION OUTPUTS ###
#######################################
@patch("qililab.automatic_calibration.calibration_node.json.dumps", autospec=True)
def test_export_calibration_outputs(mocked_dumps):
    """Test that ``export_calibration_outputs()`` works properly."""
    test_outputs = {"this_is": "a_test_dict", "foo": "bar"}
    test_dumped_outputs = '{"this_is": "a_test_dict", "foo": "bar"}'
    mocked_dumps.return_value = test_dumped_outputs
    with patch("builtins.print") as mocked_print:
        export_calibration_outputs(test_outputs)
        mocked_dumps.assert_called_with(test_outputs)
        mocked_print.assert_called_with(f"{logger_output_start}{test_dumped_outputs}")
