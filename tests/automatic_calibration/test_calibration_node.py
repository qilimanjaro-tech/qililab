"""Test for the `CalibrationNode` class"""
import os
from datetime import datetime
from io import StringIO
from typing import Callable
from unittest.mock import MagicMock, call, patch

import numpy as np
import pytest

from qililab.automatic_calibration.calibration_node import (
    CalibrationNode,
    IncorrectCalibrationOutput,
    export_calibration_outputs,
)

# pylint: disable=protected-access, unspecified-encoding

#################################################################################
#################################### SET UPS ####################################
#################################################################################

logger_output_start = "RAND_INT:47102512880765720413 - OUTPUTS: "
dummy_comparison_model = MagicMock()  # Dummy comparison model, to provide to the fixtures.


####################
### MOCKED NODES ###
####################
@pytest.fixture(name="initialize_node_no_optional")
@patch(
    "qililab.automatic_calibration.calibration_node.CalibrationNode._build_notebooks_logger_stream",
    return_value=StringIO(),
)
def fixture_initialize_node_no_optional(_) -> CalibrationNode:
    """Return a mocked CalibrationNode object for initialization, with the minimum number of things specified or mocked."""
    return CalibrationNode(
        nb_path="tests/automatic_calibration/notebook_test/zeroth.ipynb",
        qubit_index=0,
        in_spec_threshold=0.6,
        bad_data_threshold=0.9,
        comparison_model=dummy_comparison_model,
        drift_timeout=100.0,
    )


@pytest.fixture(name="initialize_node_optional")
@patch(
    "qililab.automatic_calibration.calibration_node.CalibrationNode._path_to_name_and_folder",
    return_value=("node_id", "nb_folder"),
)
@patch(
    "qililab.automatic_calibration.calibration_node.CalibrationNode.get_last_calibrated_output_parameters",
    return_value={},
)
@patch(
    "qililab.automatic_calibration.calibration_node.CalibrationNode.get_last_calibrated_timestamp",
    return_value=0.0,
)
@patch(
    "qililab.automatic_calibration.calibration_node.CalibrationNode._build_notebooks_logger_stream",
    return_value=StringIO(),
)
def fixture_initialize_node_optional(_, __, ____, _____) -> CalibrationNode:
    """Return a mocked CalibrationNode object for initialization, with everything specified or mocked."""
    return CalibrationNode(
        nb_path="tests/automatic_calibration/notebook_test/zeroth.ipynb",
        qubit_index=[0, 1],
        in_spec_threshold=0.6,
        bad_data_threshold=0.9,
        comparison_model=dummy_comparison_model,
        drift_timeout=100.0,
        input_parameters={"a": 0, "b": 1},
        sweep_interval=np.array([0, 1, 2]),
        number_of_random_datapoints=1,
    )


@pytest.fixture(name="methods_node")
@patch("qililab.automatic_calibration.calibration_node.CalibrationNode.get_last_calibrated_output_parameters")
@patch(
    "qililab.automatic_calibration.calibration_node.CalibrationNode.get_last_calibrated_timestamp", return_value=1111
)
@patch("qililab.automatic_calibration.calibration_node.StringIO", autospec=True)
def fixture_methods_node(_, __, ____) -> CalibrationNode:
    """Return a mocked CalibrationNode object."""
    return CalibrationNode(
        nb_path="./foobar.ipynb",
        qubit_index=0,
        in_spec_threshold=0.6,
        bad_data_threshold=0.9,
        comparison_model=dummy_comparison_model,
        drift_timeout=100.0,
    )


#################################################################################
############################## TESTS FOR THE CLASS ##############################
#################################################################################


###########################
### TEST INITIALIZATION ###
###########################
class TestInitializationCalibrationNode:
    """Unit tests for the CalibrationNode class initialization."""

    def test_good_init_method_without_optional(self, initialize_node_no_optional):
        """Test a valid initialization of the class, without passing optional arguments."""
        # sourcery skip: class-extract-method
        # Assert:
        assert initialize_node_no_optional.nb_path == "tests/automatic_calibration/notebook_test/zeroth.ipynb"
        assert isinstance(initialize_node_no_optional.nb_path, str)
        assert initialize_node_no_optional.qubit_index == 0
        assert isinstance(initialize_node_no_optional.qubit_index, int | list | None)
        assert initialize_node_no_optional.node_id == "zeroth_q0"
        assert isinstance(initialize_node_no_optional.nb_path, str)
        assert initialize_node_no_optional.nb_folder == "tests/automatic_calibration/notebook_test"
        assert isinstance(initialize_node_no_optional.nb_path, str)
        assert initialize_node_no_optional.in_spec_threshold == 0.6
        assert isinstance(initialize_node_no_optional.in_spec_threshold, float)
        assert initialize_node_no_optional.bad_data_threshold == 0.9
        assert isinstance(initialize_node_no_optional.bad_data_threshold, float)
        assert initialize_node_no_optional.comparison_model == dummy_comparison_model
        assert isinstance(initialize_node_no_optional.comparison_model, Callable)
        assert initialize_node_no_optional.drift_timeout == 100
        assert isinstance(initialize_node_no_optional.drift_timeout, float)
        assert initialize_node_no_optional.input_parameters is None
        assert isinstance(initialize_node_no_optional.input_parameters, dict | None)
        assert initialize_node_no_optional.sweep_interval is None
        assert isinstance(initialize_node_no_optional.sweep_interval, np.ndarray | None)
        assert initialize_node_no_optional.number_of_random_datapoints == 10
        assert isinstance(initialize_node_no_optional.number_of_random_datapoints, int)
        assert initialize_node_no_optional.output_parameters is None
        assert isinstance(initialize_node_no_optional.output_parameters, dict | None)
        assert initialize_node_no_optional.previous_output_parameters is None
        assert isinstance(initialize_node_no_optional.previous_output_parameters, dict | None)
        assert initialize_node_no_optional.previous_timestamp is None
        assert isinstance(initialize_node_no_optional.previous_timestamp, float | None)
        assert isinstance(initialize_node_no_optional._stream, StringIO)

    def test_good_init_method_with_optional(self, initialize_node_optional):
        """Test a valid initialization of the class, passing all optional arguments."""
        # Assert:
        assert initialize_node_optional.nb_path == "tests/automatic_calibration/notebook_test/zeroth.ipynb"
        assert isinstance(initialize_node_optional.nb_path, str)
        assert initialize_node_optional.qubit_index == [0, 1]
        assert isinstance(initialize_node_optional.qubit_index, int | list | None)
        assert initialize_node_optional.node_id == "node_id"
        assert isinstance(initialize_node_optional.nb_path, str)
        assert initialize_node_optional.nb_folder == "nb_folder"
        assert isinstance(initialize_node_optional.nb_path, str)
        assert initialize_node_optional.in_spec_threshold == 0.6
        assert isinstance(initialize_node_optional.in_spec_threshold, float)
        assert initialize_node_optional.bad_data_threshold == 0.9
        assert isinstance(initialize_node_optional.bad_data_threshold, float)
        assert initialize_node_optional.comparison_model == dummy_comparison_model
        assert isinstance(initialize_node_optional.comparison_model, Callable)
        assert initialize_node_optional.drift_timeout == 100
        assert isinstance(initialize_node_optional.drift_timeout, float)
        assert initialize_node_optional.input_parameters == {"a": 0, "b": 1}
        assert isinstance(initialize_node_optional.input_parameters, dict | None)
        assert initialize_node_optional.sweep_interval.all() == np.array([0, 1, 2]).all()
        assert isinstance(initialize_node_optional.sweep_interval, np.ndarray | None)
        assert initialize_node_optional.number_of_random_datapoints == 1
        assert isinstance(initialize_node_optional.number_of_random_datapoints, int)
        assert initialize_node_optional.output_parameters == {}
        assert isinstance(initialize_node_optional.output_parameters, dict | None)
        assert initialize_node_optional.previous_output_parameters is None
        assert isinstance(initialize_node_optional.previous_output_parameters, dict | None)
        assert initialize_node_optional.previous_timestamp == 0.0
        assert isinstance(initialize_node_optional.previous_timestamp, float | None)
        assert isinstance(initialize_node_optional._stream, StringIO)

    def test_bad_thresholds_initialization(self):
        """Test an invalid initialization of the class due to the thresholds.

        This happens when ``bad_data_threshold`` is smaller than ``in_spec`` one.
        """
        # Assert:
        with pytest.raises(ValueError) as error:
            _ = CalibrationNode(
                nb_path="./foobar.ipynb",
                qubit_index=0,
                in_spec_threshold=0.6,
                bad_data_threshold=0.5,
                comparison_model=dummy_comparison_model,
                drift_timeout=100,
            )
        assert str(error.value) == "`in_spec_threshold` must be smaller or equal than `bad_data_threshold`."

    def test_bad_nb_path_initialization(self):
        """Test an invalid initialization of the class due to the nb_path.

        This happens when the path doesn't follow Unix format.
        """
        # Assert:
        with pytest.raises(ValueError) as error:
            _ = CalibrationNode(
                nb_path=".bizzfuzz\\foobar.ipynb",
                qubit_index=0,
                in_spec_threshold=0.6,
                bad_data_threshold=0.7,
                comparison_model=dummy_comparison_model,
                drift_timeout=100,
            )
        assert str(error.value) == "`nb_path` must be written in unix format: `folder/subfolder/.../file.ipynb`."


class TestPublicMethodsFromCalibrationNode:
    """Unit tests for the CalibrationNode class public methods."""

    #########################
    ### TEST RUN NOTEBOOK ###
    #########################
    @pytest.mark.parametrize(
        "check, sweep_interval, input_parameters",
        [
            (True, None, {"a": 0, "b": 1}),
            (False, None, None),
            (True, np.array([1]), None),
            (False, np.array([1]), {"start": 0, "stop": 10, "step": 1}),
        ],
    )
    @patch(
        "qililab.automatic_calibration.calibration_node.CalibrationNode._build_check_data_interval",
        return_value=np.array([0]),
    )
    @patch(
        "qililab.automatic_calibration.calibration_node.CalibrationNode._execute_notebook",
        return_value={
            "check_parameters": {"x": 0, "y": 1},
            "platform_params": {"x": 0, "y": 1},
            "fidelities": {"x": 0, "y": 1},
        },
    )
    @patch(
        "qililab.automatic_calibration.calibration_node.CalibrationNode._create_notebook_datetime_path",
        return_value="",
    )
    @patch("qililab.automatic_calibration.calibration_node.os.rename")
    @patch("qililab.automatic_calibration.calibration_node.logger.error")
    def test_run_node(
        self,
        mock_logger,
        mock_os,
        mock_create,
        mock_execute,
        mock_build_cd,
        check,
        sweep_interval,
        input_parameters,
        methods_node: CalibrationNode,
    ):
        """Test that run_node works properly."""
        methods_node.sweep_interval = sweep_interval
        methods_node.input_parameters = input_parameters
        timestamp = methods_node.run_node(check)

        params_dict = (
            {"check": check}
            | {"number_of_random_datapoints": methods_node.number_of_random_datapoints}
            | {"qubit": methods_node.qubit_index}
        )

        if sweep_interval is not None:
            if check:
                params_dict |= {"sweep_interval": np.array([0])}
                mock_build_cd.assert_called_once_with()
            else:
                params_dict |= {"sweep_interval": np.array([1])}
                mock_build_cd.assert_not_called()

        if input_parameters is not None:
            params_dict |= input_parameters

        mock_create.assert_has_calls([call(methods_node.nb_path, dirty=True), call(methods_node.nb_path, timestamp)])
        mock_execute.assert_called_with(methods_node.nb_path, "", params_dict)
        mock_os.assert_called_once_with("", "")
        mock_logger.assert_not_called()

    @pytest.mark.parametrize(
        "check, sweep_interval, input_parameters",
        [
            (True, None, None),
            (False, None, {"start": 0, "stop": 10, "step": 1}),
            (True, np.array([1]), None),
            (False, np.array([1]), {"start": 0, "stop": 10, "step": 1}),
        ],
    )
    @patch(
        "qililab.automatic_calibration.calibration_node.CalibrationNode._build_check_data_interval",
        return_value=np.array([0]),
    )
    @patch("qililab.automatic_calibration.calibration_node.CalibrationNode._execute_notebook")
    @patch(
        "qililab.automatic_calibration.calibration_node.CalibrationNode._create_notebook_datetime_path",
        return_value="",
    )
    @patch("qililab.automatic_calibration.calibration_node.os.rename")
    @patch("qililab.automatic_calibration.calibration_node.logger.error")
    def test_run_node_interrupt(
        self,
        mock_logger,
        mock_os,
        mock_create,
        mock_execute,
        mock_build_cd,
        check,
        sweep_interval,
        input_parameters,
        methods_node: CalibrationNode,
    ):
        """Test that run_node works properly when a keyboard interrupt is raised."""
        mock_execute.side_effect = KeyboardInterrupt()
        with patch("qililab.automatic_calibration.calibration_node.sys.exit") as mocked_exit:
            methods_node.sweep_interval = sweep_interval
            methods_node.input_parameters = input_parameters
            methods_node.run_node(check)

        params_dict = (
            {"check": check}
            | {"number_of_random_datapoints": methods_node.number_of_random_datapoints}
            | {"qubit": methods_node.qubit_index}
        )

        if sweep_interval is not None:
            if check:
                params_dict |= {"sweep_interval": np.array([0])}
                mock_build_cd.assert_called_once_with()
            else:
                params_dict |= {"sweep_interval": np.array([1])}
                mock_build_cd.assert_not_called()

        if input_parameters is not None:
            params_dict |= input_parameters

        mock_create.assert_called_once_with(methods_node.nb_path, dirty=True)
        mock_execute.assert_called_with(methods_node.nb_path, "", params_dict)
        mock_os.assert_not_called()

        mock_logger.called_with("Interrupted automatic calibration notebook execution of %s", methods_node.nb_path)
        mocked_exit.assert_called_once_with()

    @pytest.mark.parametrize(
        "check, sweep_interval, input_parameters",
        [
            (True, None, {"start": 0, "stop": 10, "step": 1}),
            (False, None, None),
            (True, np.array([1]), {"start": 0, "stop": 10, "step": 1}),
            (False, np.array([1]), None),
        ],
    )
    @patch(
        "qililab.automatic_calibration.calibration_node.CalibrationNode._build_check_data_interval",
        return_value=np.array([0]),
    )
    @patch("qililab.automatic_calibration.calibration_node.CalibrationNode._execute_notebook")
    @patch(
        "qililab.automatic_calibration.calibration_node.CalibrationNode._create_notebook_datetime_path", return_value=""
    )
    @patch("qililab.automatic_calibration.calibration_node.os.rename")
    @patch("qililab.automatic_calibration.calibration_node.logger.error")
    def test_run_node_raises(
        self,
        mock_logger,
        mock_os,
        mock_create,
        mock_execute,
        mock_build_cd,
        check,
        sweep_interval,
        input_parameters,
        methods_node: CalibrationNode,
    ):
        """Test that run_node works properly when an exception is raised."""
        mock_execute.side_effect = ValueError("Test error")
        with patch("qililab.automatic_calibration.calibration_node.sys.exit") as mocked_exit:
            methods_node.sweep_interval = sweep_interval
            methods_node.input_parameters = input_parameters
            methods_node.run_node(check)

        params_dict = (
            {"check": check}
            | {"number_of_random_datapoints": methods_node.number_of_random_datapoints}
            | {"qubit": methods_node.qubit_index}
        )

        if sweep_interval is not None:
            if check:
                params_dict |= {"sweep_interval": np.array([0])}
                mock_build_cd.assert_called_once_with()
            else:
                params_dict |= {"sweep_interval": np.array([1])}
                mock_build_cd.assert_not_called()

        if input_parameters is not None:
            params_dict |= input_parameters

        mock_execute.assert_called_with(methods_node.nb_path, "", params_dict)
        mock_os.assert_called_once()
        assert mock_create.call_count == 2

        mock_logger.called_with(
            "Aborting execution. Exception %s during automatic calibration notebook execution, trace of the error can be found in %s",
            "Test error",
            "error_path/foobar_error.ipynb",
        )
        mocked_exit.assert_called_once_with()

    ##########################################
    ### TEST GET LAST CALIBRATED TIMESTAMP ###
    ##########################################
    @pytest.mark.parametrize("last_exec_output", [None, "tmp_test_foobar.ipynb"])
    @patch("qililab.automatic_calibration.calibration_node.CalibrationNode._find_last_executed_calibration")
    @patch("qililab.automatic_calibration.calibration_node.os.path.getmtime")
    def test_get_last_calibrated_timestamp(
        self, mocked_os, mock_last_exec, last_exec_output, methods_node: CalibrationNode
    ):
        """Test that ``get_last_executed_calibration()`` works correctly."""
        mock_last_exec.return_value = last_exec_output
        test_output = methods_node.get_last_calibrated_timestamp()
        mock_last_exec.assert_called_once()
        if last_exec_output is not None:
            mocked_os.assert_called_once()
        else:
            assert test_output is None

    ##################################################
    ### TEST GET LAST CALIBRATED OUTPUT PARAMETERS ###
    ##################################################
    @pytest.mark.parametrize("last_exec_output", [None, "tmp_test_foobar.ipynb"])
    @patch("qililab.automatic_calibration.calibration_node.CalibrationNode._parse_output_from_execution_file")
    @patch("qililab.automatic_calibration.calibration_node.CalibrationNode._find_last_executed_calibration")
    def test_get_last_calibrated_output_parameters(
        self, mock_last_exec, mocked_parse, last_exec_output, methods_node: CalibrationNode
    ):
        """Test that ``get_last_calibrated_output_parameters()`` works correctly."""
        mock_last_exec.return_value = last_exec_output
        test_output = methods_node.get_last_calibrated_output_parameters()
        mock_last_exec.assert_called_once()
        if last_exec_output is not None:
            mocked_parse.assert_called_once()
        else:
            assert test_output is None


class TestPrivateMethodsFromCalibrationNode:
    """Unit tests for the CalibrationNode class private methods."""

    #############################
    ### TEST EXECUTE NOTEBOOK ###
    #############################
    @pytest.mark.parametrize(
        "output",
        [
            'RAND_INT:47102512880765720413 - OUTPUTS: {"check_parameters": {"x": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48], "y": [100, 144, 196, 256, 324, 400, 484, 576, 676, 784, 900, 1024, 1156, 1296, 1444, 1600, 1764, 1936, 2116, 2304]}, "platform_params": [["bus_alias", "param_name", 1]]}\n',
            'RAND_INT:47102512880765720413 - OUTPUTS: {\\"check_parameters\\": {\\"x\\": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48], \\"y\\": [100, 144, 196, 256, 324, 400, 484, 576, 676, 784, 900, 1024, 1156, 1296, 1444, 1600, 1764, 1936, 2116, 2304]}, \\"platform_params\\": [[\\"bus_alias\\", \\"param_name\\", 1]]}\\n',
            'RAND_INT:47102512880765720413 - OUTPUTS: {\\"check_parameters\\": {\\"x\\": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48], \\"y\\": [100, 144, 196, 256, 324, 400, 484, 576, 676, 784, 900, 1024, 1156, 1296, 1444, 1600, 1764, 1936, 2116, 2304]}, \\"platform_params\\": [[\\"bus_alias\\", \\"param_name\\", 1]]}\\n"',
        ],
    )
    @patch("qililab.automatic_calibration.calibration_node.pm.execute_notebook")
    def test_execute_notebook(self, mocked_pm_exec, output, methods_node: CalibrationNode):
        """Testing general behavior of ``execute_notebook()``."""
        # Creating expected values for assert
        sweep_interval = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48]
        y = [i**2 for i in sweep_interval]
        results = {"x": sweep_interval, "y": y}
        expected = {"check_parameters": results, "platform_params": [["bus_alias", "param_name", 1]]}

        # Mocking return value of stream and calling execute_notebook
        methods_node._stream.getvalue.return_value = output  # type: ignore [attr-defined]
        test_value = methods_node._execute_notebook(methods_node.nb_path, "", {})

        # Asserts
        mocked_pm_exec.assert_called_once_with(
            methods_node.nb_path, "", {}, log_output=True, stdout_file=methods_node._stream
        )
        assert test_value == expected

    @pytest.mark.parametrize("output", ["", "a", "RAND_INT:4320765720413 - OUTPUTS: {'check_parameters': {'a':2}}/n"])
    @patch("qililab.automatic_calibration.calibration_node.pm.execute_notebook")
    @patch("qililab.automatic_calibration.calibration_node.logger", autospec=True)
    def test_execute_notebook_raises_no_output(self, mocked_logger, mocked_pm_exec, output, methods_node):
        """Testing when no outputs received from ``execute_notebook()``."""
        methods_node._stream.getvalue.return_value = output  # type: ignore [attr-defined]

        with pytest.raises(
            IncorrectCalibrationOutput,
            match=f"No output found, check automatic-calibration notebook in {methods_node.nb_path}",
        ):
            methods_node._execute_notebook(methods_node.nb_path, "", {})

        mocked_logger.error.assert_called_with(
            "Aborting execution. No output found, check the automatic-calibration output cell is implemented in %s",
            methods_node.nb_path,
        )

        mocked_pm_exec.assert_called_once_with(
            methods_node.nb_path, "", {}, log_output=True, stdout_file=methods_node._stream
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
    def test_execute_notebook_raises_more_than_one_output(self, mocked_logger, mocked_pm_exec, output, methods_node):
        """Testing when more than one outputs are received from ``execute_notebook()`."""
        methods_node._stream.getvalue.return_value = output  # type: ignore [attr-defined]

        with pytest.raises(
            IncorrectCalibrationOutput,
            match=f"More than one output found in {methods_node.nb_path}",
        ):
            methods_node._execute_notebook(methods_node.nb_path, "", {})

        mocked_logger.error.assert_called_with(
            "Aborting execution. More than one output found, please output the results once in %s",
            methods_node.nb_path,
        )

        mocked_pm_exec.assert_called_once_with(
            methods_node.nb_path, "", {}, log_output=True, stdout_file=methods_node._stream
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
    def test_execute_notebook_raises_empty_output(self, mocked_logger, mocked_pm_exec, output, methods_node):
        """Testing when outputs are empty received from ``execute_notebook()`."""
        methods_node._stream.getvalue.return_value = output  # type: ignore [attr-defined]

        with pytest.raises(
            IncorrectCalibrationOutput,
            match=f"Empty output found in {methods_node.nb_path}, output must have key and value 'check_parameters'.",
        ):
            methods_node._execute_notebook(methods_node.nb_path, "", {})

        mocked_logger.error.assert_called_with(
            "Aborting execution. No 'check_parameters' dictionary or its empty in the output cell implemented in %s",
            methods_node.nb_path,
        )

        mocked_pm_exec.assert_called_once_with(
            methods_node.nb_path, "", {}, log_output=True, stdout_file=methods_node._stream
        )

    ######################################
    ### TEST BUILD CHECK DATA INTERVAL ###
    ######################################
    @pytest.mark.parametrize(
        "sweep_interval, number_of_random_datapoints",
        [(np.arange(start=0, stop=5, step=1), 10), (np.arange(start=10, stop=1000, step=20), 200), (None, 1)],
    )
    def test_build_check_data_interval(
        self, methods_node: CalibrationNode, sweep_interval, number_of_random_datapoints
    ):
        """Test that ``build_check_data_interval()`` works correctly."""
        methods_node.sweep_interval = sweep_interval
        methods_node.number_of_random_datapoints = number_of_random_datapoints
        test_value = methods_node._build_check_data_interval()
        if sweep_interval is not None:
            for value in test_value:
                assert value in methods_node.sweep_interval
            assert len(test_value) == methods_node.number_of_random_datapoints
        else:
            assert test_value is None

    ##########################################
    ### TEST CREATE NOTEBOOK DATETIME PATH ###
    ##########################################
    @pytest.mark.parametrize(
        "timestamp, dirty, error",
        [(None, True, True), (145783952598, False, True), (145783959532, False, False), (None, True, False)],
    )
    def test_create_notebook_datetime_path(
        self, timestamp, dirty, error, methods_node: CalibrationNode, original_path="foo/bar.ipynb"
    ):
        """Test ``that create_notebook_datetime_path()`` works correctly."""
        with patch("qililab.automatic_calibration.calibration_node.os") as mocked_os:
            test_value = methods_node._create_notebook_datetime_path(original_path, timestamp, dirty, error)
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
                assert mocked_os.makedirs.call_count == 2
                assert "foo/error_executions/bar" in test_value
                assert "_error.ipynb" in test_value

    ####################################
    ### TEST PATH TO NAME AND FOLDER ###
    ####################################
    @pytest.mark.parametrize(
        "qubit, original_path, expected",
        [
            (0, "foo/bar/foobar.ipynb", ("foobar_q0", "foo/bar")),
            ([0, 1], "this/is/a/long/path/to/notebook.ipynb", ("notebook_q0q1", "this/is/a/long/path/to")),
        ],
    )
    def test_path_to_name_and_folder(self, methods_node: CalibrationNode, qubit, original_path, expected):
        """Test that ``path_to_name_and_folder()`` works properly."""
        methods_node.qubit_index = qubit
        test_values = methods_node._path_to_name_and_folder(original_path)
        assert len(test_values) == 2
        assert test_values[0] == expected[0]
        assert test_values[1] == expected[1]

    ###########################################
    ### TEST FIND LAST EXECUTED CALIBRATION ###
    ###########################################
    def test_find_last_executed_calibration(self, methods_node: CalibrationNode):
        """Test that ``find_last_executed_calibration()`` works correctly."""
        test_filenames = [
            "tmp_test_foobar_q0_dirty.ipynb",
            "tmp_test_foobar_q0_error.ipynb",
            "tmp_test_foo_q0_calibrated.ipynb",
            "tmp_test_bar_q0_calibrated.ipynb",
            "tmp_test_foobar_q0_.ipynb",
        ]
        filename_expected = "tmp_test_foobar_q0_calibrated.ipynb"

        for test_filename in test_filenames:
            f = open(f"{methods_node.nb_folder}/{test_filename}", "w")
            f.close()
        f = open(f"{methods_node.nb_folder}/{filename_expected}", "w")
        f.close()

        test_filename = methods_node._find_last_executed_calibration()

        assert filename_expected == test_filename

        for test_filename in test_filenames:
            os.remove(f"{methods_node.nb_folder}/{test_filename}")
        os.remove(f"{methods_node.nb_folder}/{filename_expected}")

    def test_find_last_executed_calibration_does_not_find_file(self, methods_node: CalibrationNode):
        """Test ``find_last_executed_calibration()`` works properly, when there is nothing to find."""
        test_filenames = [
            "tmp_test_foobar_dirty_q0.ipynb",
            "tmp_test_foobar_error_q0.ipynb",
            "tmp_test_foo_calibrated_q0.ipynb",
            "tmp_test_bar_calibrated_q0.ipynb",
            "tmp_test_foobar_.ipynb_q0",
        ]

        for test_filename in test_filenames:
            f = open(f"{methods_node.nb_folder}/{test_filename}", "w")
            f.close()

        test_filename = methods_node._find_last_executed_calibration()

        assert test_filename is None

        for test_filename in test_filenames:
            os.remove(f"{methods_node.nb_folder}/{test_filename}")

    #############################################
    ### TEST PARSE OUTPUT FROM EXECUTION FILE ###
    #############################################
    @pytest.mark.parametrize(
        "type_content, raw_file_contents",
        [
            (
                "good",
                'RAND_INT:47102512880765720413 - OUTPUTS: {"check_parameters": {"x": [10, 12, 14, 16, 18, 20], "y": [100, 144, 196, 256, 324, 400]}, "platform_params": [["bus_alias", "param_name", 1]]}\n',
            ),
            ("two", "RAND_INT:47102512880765720413 - OUTPUTS: /n {} RAND_INT:47102512880765720413 - OUTPUTS: {}"),
            (
                "two",
                'RAND_INT:47102512880765720413 - OUTPUTS: {"check_parameters": {"a":2}}RAND_INT:47102512880765720413 - OUTPUTS: {"check_parameters": {"a":2}}/n',
            ),
            ("none", '"check_parameters": {"x": [10, 12, 14, 16,]}'),
            (
                "two",
                'RAND_INT:47102512880765720413 - OUTPUTS: {"check_parameters": {"x": [10, 12, 14, 16, 18, 20], "y": [100, 144, 196, 256, 324, 400]}, "platform_params": [["bus_alias", "param_name", 1]]}\n'
                "\n"
                + 'RAND_INT:47102512880765720413 - OUTPUTS: {"check_parameters": {"x": [10, 12, 14, 16, 18, 20], "y": [100, 144, 196, 256, 324, 400]}, "platform_params": [["bus_alias", "param_name", 1]]}\n',
            ),
            ("empty", "RAND_INT:47102512880765720413 - OUTPUTS: {}"),
            ("empty", 'RAND_INT:47102512880765720413 - OUTPUTS: {"check_parameters":{},"y":1}'),
        ],
    )
    @patch("qililab.automatic_calibration.calibration_node.logger", autospec=True)
    def test_parse_output_from_execution_file(
        self, mocked_logger, type_content, raw_file_contents, methods_node: CalibrationNode
    ):
        """Test that ``parse_output_from_execution_file`` works correctly."""
        # Dumping the raw string of the expected dictionary on a temporary file
        filename = "tmp_test_file.ipynb"
        with open(f"{methods_node.nb_folder}/{filename}", "w") as file:
            file.write(raw_file_contents)

        if type_content == "good":
            # building a fixed dictionary for the test
            results = {"x": [10, 12, 14, 16, 18, 20], "y": [100, 144, 196, 256, 324, 400]}
            expected_dict = {"check_parameters": results, "platform_params": [["bus_alias", "param_name", 1]]}

            test_dict = methods_node._parse_output_from_execution_file(filename)
            assert test_dict == expected_dict

        if type_content == "none":
            with pytest.raises(
                IncorrectCalibrationOutput,
                match=f"No output found, check automatic-calibration notebook in {methods_node.nb_path}",
            ):
                methods_node._parse_output_from_execution_file(filename)

            mocked_logger.error.assert_called_with(
                "Aborting execution. No output found, check the automatic-calibration output cell is implemented in %s",
                methods_node.nb_path,
            )

        if type_content == "two":
            with pytest.raises(
                IncorrectCalibrationOutput,
                match=f"More than one output found in {methods_node.nb_path}",
            ):
                methods_node._parse_output_from_execution_file(filename)

            mocked_logger.error.assert_called_with(
                "Aborting execution. More than one output found, please output the results once in %s",
                methods_node.nb_path,
            )

        if type_content == "empty":
            with pytest.raises(
                IncorrectCalibrationOutput,
                match=f"Empty output found in {methods_node.nb_path}, output must have key and value 'check_parameters'.",
            ):
                methods_node._parse_output_from_execution_file(filename)

            mocked_logger.error.assert_called_with(
                "Aborting execution. No 'check_parameters' dictionary or its empty in the output cell implemented in %s",
                methods_node.nb_path,
            )

        os.remove(f"{methods_node.nb_folder}/{filename}")

    ##########################################
    ### TEST ADD STRING TO CHECKED NB NAME ###
    ##########################################
    def test_add_string_to_checked_nb_name(self, methods_node: CalibrationNode):
        """Test that ``add_string_to_checked_nb_name()`` works properly."""
        with patch("qililab.automatic_calibration.calibration_node.os.rename") as mocked_rename:
            path = f"{methods_node.nb_folder}/{methods_node.node_id}"
            timestamp_path = methods_node._create_notebook_datetime_path(path, 0).split(".ipynb")[0]
            string_to_add = "test_succesful"
            methods_node._add_string_to_checked_nb_name(string_to_add, 0)
            mocked_rename.assert_called_once_with(f"{timestamp_path}.ipynb", f"{timestamp_path}_{string_to_add}.ipynb")

    ##############################################
    ### TEST INVERT OUTPUT AND PREVIOUS OUTPUT ###
    ##############################################
    def test_invert_output_and_previous_output(self, methods_node: CalibrationNode):
        """Test that ``invert_output_and_previous_output()`` work properly."""
        test_output_params = {"test_output_params": "foo"}
        test_previous_output_params = {"test_previous_output_params": "bar"}
        methods_node.output_parameters, methods_node.previous_output_parameters = (
            test_output_params,
            test_previous_output_params,
        )
        methods_node._invert_output_and_previous_output()
        assert methods_node.output_parameters == test_previous_output_params
        assert methods_node.previous_output_parameters == test_output_params


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