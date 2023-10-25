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

    # TODO: Init test, mockear init fucntions calls and check their calls


@pytest.fixture(name="ccnode")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_output_parameters")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_timestamp")
def fixture_ccnode(mocked_last_cal_params, mocked_last_cal_time) -> CalibrationNode:
    """Return a simple CalibrationNode object"""

    # TODO: rename to public methods fixture
    def dummy():
        pass

    dummy_cmp_model = dummy
    return CalibrationNode(
        nb_path="./foobar.ipynb",
        in_spec_threshold=0.6,
        bad_data_threshold=0.9,
        comparison_model=dummy_cmp_model,
        drift_timeout=100,
    )


class TestCalibrationNode:
    """Unit tests for the CalibrationNode class methods"""

    def test_add_string_to_checked_nb_name(self, ccnode: CalibrationNode):
        with patch("qililab.automatic_calibration.calibration_node.os.rename") as mocked_rename:
            path = f"{ccnode.nb_folder}/{ccnode.node_id}"
            timestamp_path = ccnode._create_notebook_datetime_path(path, 0).split(".ipynb")[0]
            string_to_add = "test_succesfull"
            ccnode.add_string_to_checked_nb_name(string_to_add, 0)
            mocked_rename.assert_called_once_with(f"{timestamp_path}.ipynb", f"{timestamp_path}_{string_to_add}.ipynb")

    # def test_run_notebook():
    #     #TODO: do all

    def test_invert_output_and_previous_output(self, ccnode: CalibrationNode):
        test_output_params = {"test_output_params": "foo"}
        test_previous_output_params = {"test_previous_output_params": "bar"}
        ccnode.output_parameters, ccnode.previous_output_parameters = (
            test_output_params,
            test_previous_output_params,
        )
        ccnode.invert_output_and_previous_output()
        assert ccnode.output_parameters == test_previous_output_params
        assert ccnode.previous_output_parameters == test_output_params

    # TODO: This tests fails as the patch is currently not working :(
    @patch("qililab.automatic_calibration.calibration_node.json.dumps", autospec=True)
    def test_export_calibration_outputs(self, ccnode: CalibrationNode, mocked_dumps):
        test_outputs = {"this_is": "a_test_dict", "foo": "bar"}
        test_dumped_outputs = '{"this_is": "a_test_dict", "foo": "bar"}'
        with patch("builtins.print") as mocked_print:
            ccnode.export_calibration_outputs(test_outputs)
            mocked_dumps.assert_called_with(test_outputs)
            mocked_print.assert_called_with(f"{logger_output_start}{test_dumped_outputs}")


@pytest.fixture(name="cnode")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_output_parameters")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_timestamp")
@patch("qililab.automatic_calibration.calibration_node.StringIO", autospec=True)
def fixture_cnode(mocked_last_cal_params, mocked_last_cal_time, mocked_stringio) -> CalibrationNode:
    """Return a simple CalibrationNode object"""

    # TODO: rename to private methods fixture
    def dummy():
        pass

    dummy_cmp_model = dummy
    return CalibrationNode(
        nb_path="./foobar.ipynb",
        in_spec_threshold=0.6,
        bad_data_threshold=0.9,
        comparison_model=dummy_cmp_model,
        drift_timeout=100,
    )


class TestCalibrationNodePrivate:
    """Unit tests for the CalibrationNode class private methods"""

    @pytest.mark.parametrize(
        "sweep_interval, expected",
        [(None, None), ({"start": 0, "stop": 5, "step": 1}, [0, 1, 2, 3, 4])],
    )
    def test_sweep_interval_as_array(self, cnode: CalibrationNode, sweep_interval, expected):
        cnode.sweep_interval = sweep_interval
        test_value = cnode._sweep_interval_as_array()
        assert test_value == expected

    @pytest.mark.parametrize(
        "sweep_interval, number_of_random_datapoints",
        [({"start": 0, "stop": 5, "step": 1}, 10), ({"start": 10, "stop": 1000, "step": 20}, 200)],
    )
    def test_build_check_data_interval(self, cnode: CalibrationNode, sweep_interval, number_of_random_datapoints):
        cnode.sweep_interval = sweep_interval
        cnode.number_of_random_datapoints = number_of_random_datapoints
        sweep_interval_range = np.arange(sweep_interval["start"], sweep_interval["stop"], sweep_interval["step"])
        test_value = cnode._build_check_data_interval()
        assert len(test_value) == cnode.number_of_random_datapoints
        for value in test_value:
            assert value in sweep_interval_range

    # TODO: This tests fails as the papermill patch is currently not working :(
    @patch("qililab.automatic_calibration.calibration_node.CalibrationNode.pm.execute_notebook")
    def test_execute_notebook(self, cnode: CalibrationNode, mocked_pm):
        raw_file_contents = "RAND_INT:47102512880765720413 - OUTPUTS: {check_parameters: {x: [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48], y: [100, 144, 196, 256, 324, 400, 484, 576, 676, 784, 900, 1024, 1156, 1296, 1444, 1600, 1764, 1936, 2116, 2304]}, platform_params: [[bus_alias, param_name, 1]]}"

        sweep_interval = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48]
        y = [i**2 for i in sweep_interval]
        results = {"x": sweep_interval, "y": y}
        expected = {"check_parameters": results, "platform_params": [["bus_alias", "param_name", 1]]}

        cnode.stream.getvalue.return_value = raw_file_contents
        test_value = cnode._execute_notebook(cnode.nb_path, "", {})
        mocked_pm.execute_notebook.assert_called_once()
        assert test_value == expected

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
    #               # TODO: define multipleoutputs
    #            mocked_logger.info.assert_called_with("Aborting execution. More than one output found, please output the results once in %s",
    #                input_path)
    #            (msg,) = multiple_out_err.value.args
    #            assert msg == f"More than one output found in {input_path}"
    #
    #    @patch("qililab.automatic_calibration.calibration_node.papermill",autospec=True)
    #    @patch("qililab.automatic_calibration.calibration_node.io.StringIO",autospec=True)
    #    def test_execute_notebook_raises_incorrect_output(self, cnode, input_path, output_path, parameters, mocked_papermill, mocked_stream, output):
    #        mocked_stream.return_value = output
    # TODO: Output without check_parameter in it, or is empty. (Do both cases)
    #        with pytest.raises(IncorrectCalibrationOutput) as incorrect_out_err:
    #            cnode._execute_notebook(self, input_path, output_path, parameters)
    #
    #            (msg,) = incorrect_out_err.value.args
    #            assert msg == f"Calibration output must have key and value 'check_parameters' in notebook {input_path}"
    #
    #    def test_get_last_calibrated_timestamp():
    #        pass
    #
    #    def test_get_last_calibrated_output_parameters():
    #        pass

    def test_parse_output_from_execution_file(self, cnode: CalibrationNode):
        # building a fixed dictionary for the test
        sweep_interval = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48]
        y = [i**2 for i in sweep_interval]
        results = {"x": sweep_interval, "y": y}
        expected_dict = {"check_parameters": results, "platform_params": [["bus_alias", "param_name", 1]]}

        # Dumping the raw string of the expected dictionary on a temporary file
        raw_file_contents = 'RAND_INT:47102512880765720413 - OUTPUTS: {"check_parameters": {"x": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48], "y": [100, 144, 196, 256, 324, 400, 484, 576, 676, 784, 900, 1024, 1156, 1296, 1444, 1600, 1764, 1936, 2116, 2304]}, "platform_params": [["bus_alias", "param_name", 1]]}\n'
        filename = "tmp_test_file.ipynb"
        with open(f"{cnode.nb_folder}/{filename}", "w") as file:
            file.write(raw_file_contents)

        test_dict = cnode._parse_output_from_execution_file(filename)
        assert test_dict == expected_dict
        os.remove(f"{cnode.nb_folder}/{filename}")

    # TODO: add here comment staring new method testing, and same for all methods
    def test_find_last_executed_calibration(self, cnode: CalibrationNode):
        test_filenames = [
            "tmp_test_foobar_dirty.ipynb",
            "tmp_test_foobar_error.ipynb",
            "tmp_test_foo_calibrated.ipynb",
            "tmp_test_bar_calibrated.ipynb",
            "tmp_test_foobar_.ipynb",
        ]
        filename_expected = "tmp_test_foobar_calibrated.ipynb"

        for test_filename in test_filenames:
            f = open(f"{cnode.nb_folder}/{test_filename}", "w")
            f.close()
        f = open(f"{cnode.nb_folder}/{filename_expected}", "w")
        f.close()

        test_filename = cnode._find_last_executed_calibration()

        assert filename_expected == test_filename

        for test_filename in test_filenames:
            os.remove(f"{cnode.nb_folder}/{test_filename}")
        os.remove(f"{cnode.nb_folder}/{filename_expected}")

    def test_find_last_executed_calibration_does_not_find_file(self, cnode: CalibrationNode):
        test_filenames = [
            "tmp_test_foobar_dirty.ipynb",
            "tmp_test_foobar_error.ipynb",
            "tmp_test_foo_calibrated.ipynb",
            "tmp_test_bar_calibrated.ipynb",
            "tmp_test_foobar_.ipynb",
        ]

        for test_filename in test_filenames:
            f = open(f"{cnode.nb_folder}/{test_filename}", "w")
            f.close()

        test_filename = cnode._find_last_executed_calibration()

        assert test_filename is None

        for test_filename in test_filenames:
            os.remove(f"{cnode.nb_folder}/{test_filename}")


@pytest.fixture(name="node_class")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_output_parameters")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode._get_last_calibrated_timestamp")
def fixture_node_class(mocked_last_cal_params, mocked_last_cal_time) -> CalibrationNode:
    """Return a simple CalibrationNode object"""

    # TODO: change name to class and static methods
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


# TODO: Change name to class and static
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


# TODO: rename static methods
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
