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

from qililab.automatic_calibration.calibration_node import CalibrationNode, IncorrectCalibrationOutput
from qililab.config import logger

logger_output_start = "RAND_INT:47102512880765720413 - OUTPUTS: "


class TestCalibrationNodeInitialization:
    """Unit tests for the CalibrationNode class initialization"""


# class TestCalibrationNode:
#    """Unit tests for the CalibrationNode class methods"""
#    def test_add_string_to_checked_nb_name():
#    def test_run_notebook():
#    def test_invert_output_and_previous_output():
#    def test_export_calibration_outputs():
#
# class TestCalibrationNodePrivate:
#    """Unit tests for the CalibrationNode class private methods"""
#    @pytest.mark.parametrize(
#        "sweep_interval","expected",
#        [(None, None), ({"start":0, "stop":5, "step":1}, [0,1,2,3,4])],
#    )
#    def test_sweep_interval_as_array(self, cnode, sweep_interval, expected):
#        cnode.sweep_interval = sweep_interval
#        test_value = cnode._sweep_interval()
#        assert test_value == expected
#
#
#    def test_build_check_data_interval(self, cnode, sweep_interval):
#        cnode.sweep_interval = sweep_interval
#        sweep_interval_range = np.arange(sweep_interval['start'],sweep_interval['stop'],sweep_interval['step'])
#        test_value = cnode._build_check_data_interval()
#        assert len(test_value) == cnode.number_of_random_datapoints
#        for value in test_value:
#            assert value in sweep_interval_range
#
#    @patch("qililab.automatic_calibration.calibration_node.papermill",autospec=True)
#    @patch("qililab.automatic_calibration.calibration_node.io.StringIO",autospec=True)
#    def test_execute_notebook(self, cnode, input_path, output_path, parameters, mocked_papermill, mocked_stream, output, expected):
#        mocked_stream.return_value = output
#        test_value = cnode._execute_notebook(self, input_path, output_path, parameters)
#        mocked_papermill.execute_notebook.assert_called_once()
#        assert test_value == expected
#
#    @patch("qililab.automatic_calibration.calibration_node.papermill",autospec=True)
#    @patch("qililab.automatic_calibration.calibration_node.io.StringIO",autospec=True)
#    @patch("qililab.automatic_calibration.calibration_node.logger",autospec=True)
#    def test_execute_notebook_raises_no_output(self, cnode, input_path, output_path, parameters, mocked_papermill, mocked_stream, mocked_logger, output):
#        mocked_stream.return_value = output
#        with pytest.raises(IncorrectCalibrationOutput) as no_out_err:
#            cnode._execute_notebook(self, input_path, output_path, parameters)
#
#            mocked_logger.info.assert_called_with("Aborting execution. More than one output found, please output the results once in %s",
#                input_path)
#            (msg,) = no_out_err.value.args
#            assert msg == f"No output found, check autocalibation notebook in {input_path}"
#
#    @patch("qililab.automatic_calibration.calibration_node.papermill",autospec=True)
#    @patch("qililab.automatic_calibration.calibration_node.io.StringIO",autospec=True)
#    @patch("qililab.automatic_calibration.calibration_node.logger",autospec=True)
#    def test_execute_notebook_raises_multiple_output(self, cnode, input_path, output_path, parameters, mocked_papermill, mocked_stream, mocked_logger, output):
#        mocked_stream.return_value = output
#        with pytest.raises(IncorrectCalibrationOutput) as multiple_out_err:
#            cnode._execute_notebook(self, input_path, output_path, parameters)
#
#            mocked_logger.info.assert_called_with("Aborting execution. More than one output found, please output the results once in %s",
#                input_path)
#            (msg,) = multiple_out_err.value.args
#            assert msg == f"More than one output found in {input_path}"
#
#    @patch("qililab.automatic_calibration.calibration_node.papermill",autospec=True)
#    @patch("qililab.automatic_calibration.calibration_node.io.StringIO",autospec=True)
#    def test_execute_notebook_raises_incorrect_output(self, cnode, input_path, output_path, parameters, mocked_papermill, mocked_stream, output):
#        mocked_stream.return_value = output
#        with pytest.raises(IncorrectCalibrationOutput) as incorrect_out_err:
#            cnode._execute_notebook(self, input_path, output_path, parameters)
#
#            (msg,) = incorrect_out_err.value.args
#            assert msg == f"Calibration output must have key and value 'check_parameters' in notebook {input_path}"
#
#    def test_get_last_calibrated_timestamp():
#    def test_get_last_calibrated_output_parameters():
#    def test_parse_output_from_execution_file():
#    def test_find_last_executed_calibration():


@pytest.fixture(name="node_class")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_output_parameters")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_timestamp")
def fixture_node_class(mocked_last_cal_params, mocked_last_cal_time) -> CalibrationNode:
    """Return a simple CalibrationNode object"""

    def dummy():
        pass

    dummy_cmp_model = dummy
    return CalibrationNode(
        nb_path="foo/bar.ipynb",
        in_spec_threshold=0.6,
        bad_data_threshold=0.9,
        comparison_model=dummy_cmp_model,
        drift_timeout=100,
    )


class TestCalibrationNodeClass:
    """Test the class methods of the `CalibrationNode`class"""

    @pytest.mark.parametrize(
        "timestamp, dirty, error",
        [(None, True, True), (145783952598, False, True), (145783959532, False, False), (None, True, False)],
    )
    def test_create_notebook_datetime_path(
        self, node_class: CalibrationNode, timestamp, dirty, error, original_path="foo/bar.ipynb"
    ):
        with patch("qililab.automatic_calibration.calibration_node.os") as mocked_os:
            test_value = node_class._create_notebook_datetime_path(original_path, timestamp, dirty, error)
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


class TestCalibrationNodeStatic:
    """Test static methods of the `CalibrationNode` class"""

    @patch("qililab.automatic_calibration.calibration_node.logging", autospec=True)
    def test_build_notebooks_logger_stream(self, mocked_logging):
        stream = CalibrationNode._build_notebooks_logger_stream()
        mocked_logging.basicConfig.assert_called_once()
        assert isinstance(stream, StringIO)

    @pytest.mark.parametrize(
        "original_path, expected",
        [
            ("foo/bar/foobar.ipynb", ("foobar", "foo/bar")),
            ("this/is/a/long/path/to/notebook.ipynb", ("notebook", "this/is/a/long/path/to")),
        ],
    )
    def test_path_to_name_and_folder(self, original_path, expected):
        test_values = CalibrationNode._path_to_name_and_folder(original_path)
        assert len(test_values) == 2
        assert test_values[0] == expected[0]
        assert test_values[1] == expected[1]

    @patch("qililab.automatic_calibration.calibration_node.datetime", autospec=True)
    def test_get_timestamp(self, modked_datetime):
        CalibrationNode._get_timestamp()
        modked_datetime.now.assert_called_once()
        modked_datetime.timestamp.assert_called_once()
