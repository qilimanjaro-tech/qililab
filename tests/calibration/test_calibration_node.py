"""Test for the `CalibrationNode` class"""

import os
from datetime import datetime
from io import StringIO
from unittest.mock import MagicMock, call, patch

import numpy as np
import pytest

from qililab.calibration.calibration_node import CalibrationNode, _json_serialize, export_nb_outputs

#################################################################################
# SET UPS ####################################
#################################################################################

logger_output_start = "RAND_INT:47102512880765720413 - OUTPUTS: "
dummy_comparison_model = MagicMock()  # Dummy comparison model, to provide to the fixtures.


####################
# MOCKED NODES ###
####################
@pytest.fixture(name="initialize_node_no_optional")
def fixture_initialize_node_no_optional() -> CalibrationNode:
    """Return a mocked CalibrationNode object for initialization, with the minimum number of things specified or mocked."""
    return CalibrationNode(
        nb_path="tests/calibration/notebook_test/zeroth.ipynb",
        qubit_index=0,
    )


@pytest.fixture(name="initialize_node_optional")
@patch(
    "qililab.calibration.calibration_node.CalibrationNode.get_last_calibrated_timestamp",
    return_value=0.0,
)
def fixture_initialize_node_optional(_) -> CalibrationNode:
    """Return a mocked CalibrationNode object for initialization, with everything specified or mocked."""
    return CalibrationNode(
        nb_path="tests/calibration/notebook_test/zeroth.ipynb",
        qubit_index=[0, 1],
        node_distinguisher=1,
        input_parameters={"a": 0, "b": 1},
        sweep_interval=np.array([0, 1, 2]),
    )


@pytest.fixture(name="methods_node")
@patch("qililab.calibration.calibration_node.CalibrationNode.get_last_calibrated_timestamp", return_value=1111)
@patch("qililab.calibration.calibration_node.StringIO", autospec=True)
def fixture_methods_node(_, __) -> CalibrationNode:
    """Return a mocked CalibrationNode object."""
    return CalibrationNode(
        nb_path="./foobar.ipynb",
        qubit_index=0,
    )


@pytest.fixture(name="methods_node_run", params=[0, [0, 2]])
@patch("qililab.calibration.calibration_node.CalibrationNode.get_last_calibrated_timestamp", return_value=1111)
@patch("qililab.calibration.calibration_node.StringIO", autospec=True)
def fixture_methods_node_run(_, __, request: pytest.FixtureRequest) -> CalibrationNode:
    """Return a mocked CalibrationNode object."""
    return CalibrationNode(
        nb_path="./foobar.ipynb",
        qubit_index=request.param,
    )


def side_efect_execute_create_file_and_raise(*args, **kwargs):
    """Generates a dummy file and raises an exception"""
    os.close(os.open("foobar_q0_dirty.ipynb", os.O_CREAT))
    raise ValueError("Test error")


#################################################################################
# TESTS FOR THE CLASS ##############################
#################################################################################


###########################
# TEST INITIALIZATION ###
###########################
class TestInitializationCalibrationNode:
    """Unit tests for the CalibrationNode class initialization."""

    def test_good_init_method_without_optional(self, initialize_node_no_optional):
        """Test a valid initialization of the class, without passing optional arguments."""
        # sourcery skip: class-extract-method
        # Assert:
        assert initialize_node_no_optional.nb_path == os.path.abspath("tests/calibration/notebook_test/zeroth.ipynb")
        assert initialize_node_no_optional.qubit_index == 0
        assert initialize_node_no_optional.node_distinguisher is None
        assert initialize_node_no_optional.node_id == "zeroth_q0"
        assert initialize_node_no_optional.nb_folder == os.path.abspath("tests/calibration/notebook_test")
        assert initialize_node_no_optional.input_parameters is None
        assert initialize_node_no_optional.sweep_interval is None
        assert initialize_node_no_optional.output_parameters is None
        assert initialize_node_no_optional.previous_timestamp is None
        assert isinstance(initialize_node_no_optional._stream, StringIO)
        assert initialize_node_no_optional.been_calibrated is False

    def test_good_init_method_with_optional(self, initialize_node_optional):
        """Test a valid initialization of the class, passing all optional arguments."""
        # Assert:
        assert initialize_node_optional.nb_path == os.path.abspath("tests/calibration/notebook_test/zeroth.ipynb")
        assert initialize_node_optional.qubit_index == [0, 1]
        assert initialize_node_optional.node_distinguisher == 1
        assert initialize_node_optional.node_id == "zeroth_1_q0q1"
        assert initialize_node_optional.nb_folder == os.path.abspath("tests/calibration/notebook_test")
        assert initialize_node_optional.input_parameters == {"a": 0, "b": 1}
        assert initialize_node_optional.sweep_interval.all() == np.array([0, 1, 2]).all()
        assert initialize_node_optional.output_parameters is None
        assert initialize_node_optional.previous_timestamp == 0.0
        assert isinstance(initialize_node_optional._stream, StringIO)
        assert initialize_node_optional.been_calibrated is False

    def test_bad_nb_path_initialization(self):
        """Test an invalid initialization of the class due to the nb_path.

        This happens when the path doesn't follow Unix format.
        """
        # Assert:
        with pytest.raises(ValueError) as error:
            _ = CalibrationNode(
                nb_path=".bizzfuzz\\foobar.ipynb",
                qubit_index=0,
            )
        assert str(error.value) == "`nb_path` must be written in unix format: `folder/subfolder/.../file.ipynb`."

    def test_bad_qubit_index_initialization(self):
        """Test an invalid initialization of the class due to `qubit_index`.

        This happens when the `qubit_index` is a list not having exactly two elements.
        """
        # Assert:
        with pytest.raises(ValueError) as error:
            _ = CalibrationNode(
                nb_path=".bizzfuzz/foobar.ipynb",
                qubit_index=[0, 1, 2],
            )
        assert str(error.value) == "List of `qubit_index` only accepts two qubit index"


class TestPublicMethodsFromCalibrationNode:
    """Unit tests for the CalibrationNode class public methods."""

    #########################
    # TEST RUN NOTEBOOK ###
    #########################

    @pytest.mark.parametrize(
        "sweep_interval, input_parameters, json_serialize_return",
        [
            (None, {"a": 0, "b": 1}, {"a": 0, "b": 1}),
            (None, None, {}),
            ([1], None, {"sweep_interval": [1]}),
            (
                [1],
                {"start": 0, "stop": 10, "step": 1},
                {"sweep_interval": [1], "start": 0, "stop": 10, "step": 1},
            ),
        ],
    )
    @patch(
        "qililab.calibration.calibration_node.CalibrationNode._execute_notebook",
        return_value={
            "platform_parameters": {"x": 0, "y": 1},
            "fidelities": {"x": 0, "y": 1},
        },
    )
    @patch(
        "qililab.calibration.calibration_node.CalibrationNode._create_notebook_datetime_path",
        return_value="",
    )
    @patch("qililab.calibration.calibration_node.os.rename")
    @patch("qililab.calibration.calibration_node.logger.error")
    @patch("qililab.calibration.calibration_node._json_serialize")
    def test_run_node(
        self,
        mock_json_serialize,
        mock_logger,
        mock_os,
        mock_create,
        mock_execute,
        sweep_interval,
        input_parameters,
        json_serialize_return,
        methods_node_run: CalibrationNode,
    ):
        """Test that run_node works properly."""
        if isinstance(methods_node_run.qubit_index, int):
            test_qubit_dict = {"qubit": methods_node_run.qubit_index}
        elif isinstance(methods_node_run.qubit_index, list):
            test_qubit_dict = {
                "control_qubit": methods_node_run.qubit_index[0],
                "target_qubit": methods_node_run.qubit_index[1],
            }
        test_params_dict = json_serialize_return | test_qubit_dict

        mock_json_serialize.return_value = test_params_dict
        methods_node_run.sweep_interval = sweep_interval
        methods_node_run.input_parameters = input_parameters
        timestamp = methods_node_run.run_node()

        mock_create.assert_has_calls([call(dirty=True), call(timestamp=timestamp)])
        mock_json_serialize.assert_called_once_with(test_params_dict)
        mock_execute.assert_called_with(methods_node_run.nb_path, "", test_params_dict)
        mock_os.assert_called_once_with("", "")
        mock_logger.assert_not_called()

        assert methods_node_run.output_parameters == mock_execute.return_value

    @pytest.mark.parametrize(
        "sweep_interval, input_parameters, json_serialize_return",
        [
            (None, None, {"qubit": 0}),
            (None, {"start": 0, "stop": 10, "step": 1}, {"qubit": 0, "start": 0, "stop": 10, "step": 1}),
            (np.array([1]), None, {"qubit": 0, "sweep_interval": [1]}),
            (
                np.array([1]),
                {"start": 0, "stop": 10, "step": 1},
                {"qubit": 0, "sweep_interval": [1], "start": 0, "stop": 10, "step": 1},
            ),
        ],
    )
    @patch("qililab.calibration.calibration_node.CalibrationNode._execute_notebook")
    @patch(
        "qililab.calibration.calibration_node.CalibrationNode._create_notebook_datetime_path",
        return_value="",
    )
    @patch("qililab.calibration.calibration_node.os.rename")
    @patch("qililab.calibration.calibration_node.logger.error")
    @patch("qililab.calibration.calibration_node._json_serialize")
    def test_run_node_interrupt(
        self,
        mock_json_serialize,
        mock_logger,
        mock_os,
        mock_create,
        mock_execute,
        sweep_interval,
        input_parameters,
        json_serialize_return,
        methods_node: CalibrationNode,
    ):
        """Test that run_node works properly when a keyboard interrupt is raised."""
        mock_json_serialize.return_value = json_serialize_return
        mock_execute.side_effect = KeyboardInterrupt()
        with pytest.raises(
            KeyboardInterrupt,
            match=f"Interrupted automatic calibration notebook execution of {methods_node.nb_path}",
        ):
            methods_node.sweep_interval = sweep_interval
            methods_node.input_parameters = input_parameters
            methods_node.run_node()

        params_dict = {"qubit": methods_node.qubit_index}

        if sweep_interval is not None:
            params_dict |= {"sweep_interval": np.array([1])}

        if input_parameters is not None:
            params_dict |= input_parameters

        mock_create.assert_called_once_with(dirty=True)
        mock_json_serialize.assert_called_once_with(params_dict)
        mock_execute.assert_called_with(methods_node.nb_path, "", params_dict)
        mock_os.assert_not_called()

        mock_logger.called_with("Interrupted automatic calibration notebook execution of %s", methods_node.nb_path)

    @pytest.mark.parametrize(
        "sweep_interval, input_parameters",
        [
            (None, {"start": 0, "stop": 10, "step": 1}),
            (None, None),
            (np.array([1]), {"start": 0, "stop": 10, "step": 1}),
            (np.array([1]), None),
        ],
    )
    @patch("qililab.calibration.calibration_node.CalibrationNode._execute_notebook")
    @patch("qililab.calibration.calibration_node.CalibrationNode._create_notebook_datetime_path", return_value="")
    @patch("qililab.calibration.calibration_node.logger.error")
    def test_run_node_raises(
        self,
        mock_logger,
        mock_create,
        mock_execute,
        sweep_interval,
        input_parameters,
        methods_node: CalibrationNode,
    ):
        """Test that run_node works properly when an exception is raised."""
        mock_execute.side_effect = ValueError("Test error")
        with pytest.raises(Exception):
            methods_node.sweep_interval = sweep_interval
            methods_node.input_parameters = input_parameters
            methods_node.run_node()

        params_dict = {"qubit": methods_node.qubit_index}

        if sweep_interval is not None:
            params_dict |= {"sweep_interval": np.array([1])}

        if input_parameters is not None:
            params_dict |= input_parameters

        mock_execute.assert_called_with(methods_node.nb_path, "", params_dict)
        assert mock_create.call_count == 1

        mock_logger.called_with(
            "Aborting execution. Exception %s during automatic calibration notebook execution, trace of the error can be found in %s",
            "Test error",
            "error_path/foobar_error.ipynb",
        )

    @pytest.mark.parametrize(
        "sweep_interval, input_parameters",
        [
            (None, {"start": 0, "stop": 10, "step": 1}),
            (None, None),
            (np.array([1]), {"start": 0, "stop": 10, "step": 1}),
            (np.array([1]), None),
        ],
    )
    @patch(
        "qililab.calibration.calibration_node.CalibrationNode._execute_notebook",
        side_effect=side_efect_execute_create_file_and_raise,
    )
    @patch(
        "qililab.calibration.calibration_node.CalibrationNode._create_notebook_datetime_path",
        return_value=f"{os.getcwd()}/foobar_q0_dirty.ipynb",
    )
    @patch("qililab.calibration.calibration_node.logger.error")
    def test_run_node_raises_error_from_execution(
        self,
        mock_logger,
        mock_create,
        mock_execute,
        sweep_interval,
        input_parameters,
        methods_node: CalibrationNode,
    ):
        """Test that run_node works properly when an exception is raised and the error notebook file is created."""
        with pytest.raises(Exception):
            methods_node.sweep_interval = sweep_interval
            methods_node.input_parameters = input_parameters
            methods_node.run_node()
        # Remove created file from the mock
        os.remove(f"{os.getcwd()}/foobar_q0_dirty.ipynb")

        params_dict = {"qubit": methods_node.qubit_index}

        if sweep_interval is not None:
            params_dict |= {"sweep_interval": np.array([1])}

        if input_parameters is not None:
            params_dict |= input_parameters

        mock_execute.assert_called_with(methods_node.nb_path, f"{os.getcwd()}/foobar_q0_dirty.ipynb", params_dict)
        assert mock_create.call_count == 2

        mock_logger.called_with(
            "Aborting execution. Exception %s during automatic calibration notebook execution, trace of the error can be found in %s",
            "Test error",
            f"{os.getcwd()}/foobar_q0_dirty.ipynb",
        )

    @patch(
        "qililab.calibration.calibration_node.CalibrationNode._execute_notebook",
        side_effect=Exception("test_exception"),
    )
    @patch("qililab.calibration.calibration_node.logger", autospec=True)
    @patch("qililab.calibration.calibration_node.os")
    def test_run_node_does_not_rename_non_existent_output(self, mocked_os, mocked_logger, _, methods_node):
        """Testing when outputs are empty received from ``execute_notebook()`."""
        with pytest.raises(
            Exception,
            match="Aborting execution. Exception test_exception during automatic calibration, expected error execution file to be created but it did not",
        ):
            methods_node.run_node()

        mocked_os.assert_not_called()
        mocked_logger.error.assert_called_with(
            "Aborting execution. Exception %s during automatic calibration, expected error execution file to be created but it did not",
            "test_exception",
        )

    ##########################################
    # TEST GET LAST CALIBRATED TIMESTAMP ###
    ##########################################
    @pytest.mark.parametrize("last_exec_output", [None, "tmp_test_foobar.ipynb"])
    @patch("qililab.calibration.calibration_node.CalibrationNode._find_last_executed_calibration")
    @patch("qililab.calibration.calibration_node.os.path.getmtime")
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


class TestPrivateMethodsFromCalibrationNode:
    """Unit tests for the CalibrationNode class private methods."""

    #############################
    # TEST EXECUTE NOTEBOOK ###
    #############################
    @pytest.mark.parametrize(
        "output",
        [
            'RAND_INT:47102512880765720413 - OUTPUTS: {"platform_parameters": [["bus_alias", "param_name", 1]]}\n',
            'RAND_INT:47102512880765720413 - OUTPUTS: {\\"platform_parameters\\": [[\\"bus_alias\\", \\"param_name\\", 1]]}\\n',
            'RAND_INT:47102512880765720413 - OUTPUTS: {\\"platform_parameters\\": [[\\"bus_alias\\", \\"param_name\\", 1]]}\\n"',
        ],
    )
    @patch("qililab.calibration.calibration_node.pm.execute_notebook")
    @patch("qililab.calibration.calibration_node.os.chdir")
    @patch("qililab.calibration.calibration_node.os.getcwd")
    def test_execute_notebook(
        self, mocked_os_getcwd, mocked_os_chdir, mocked_pm_exec, output, methods_node: CalibrationNode
    ):
        """Testing general behavior of ``execute_notebook()``."""
        # Creating expected values for assert
        expected = {"platform_parameters": [["bus_alias", "param_name", 1]]}

        # Mocking return value of stream and calling execute_notebook
        methods_node._stream.getvalue.return_value = output  # type: ignore[attr-defined]
        test_value = methods_node._execute_notebook(methods_node.nb_path, "", {})

        # Asserts
        mocked_os_getcwd.assert_called_once()
        assert mocked_os_chdir.call_count == 2
        mocked_pm_exec.assert_called_once_with(
            methods_node.nb_path, "", {}, log_output=True, stdout_file=methods_node._stream
        )
        assert test_value == expected

    @patch("qililab.calibration.calibration_node.pm.execute_notebook")
    @patch("qililab.calibration.calibration_node.os.chdir")
    @patch("qililab.calibration.calibration_node.os.getcwd")
    def test_execute_notebook_without_output(
        self, mocked_os_getcwd, mocked_os_chdir, mocked_pm_exec, methods_node: CalibrationNode
    ):
        """Testing general behavior of ``execute_notebook()``."""
        # Creating expected values for assert

        # Mocking return value of stream and calling execute_notebook
        methods_node._stream.getvalue.return_value = ""  # type: ignore[attr-defined]
        test_value = methods_node._execute_notebook(methods_node.nb_path, "", {})

        # Asserts
        mocked_os_getcwd.assert_called_once()
        assert mocked_os_chdir.call_count == 2
        mocked_pm_exec.assert_called_once_with(
            methods_node.nb_path, "", {}, log_output=True, stdout_file=methods_node._stream
        )
        assert methods_node.output_parameters == test_value is None

    @pytest.mark.parametrize(
        "output",
        [
            'RAND_INT:47102512880765720413 - OUTPUTS: {"platform_parameters": {"fizz":"buzz"}} RAND_INT:47102512880765720413 - OUTPUTS: {"platform_parameters": {"foo": "bar"}}',
            'RAND_INT:47102512880765720413 - OUTPUTS: {"platform_parameters": {"a":2}}RAND_INT:47102512880765720413 - OUTPUTS: {"platform_parameters": {"a":2}}RAND_INT:47102512880765720413 - OUTPUTS: {"platform_parameters": {"a":2}}/n',
        ],
    )
    @patch("qililab.calibration.calibration_node.pm.execute_notebook")
    @patch("qililab.calibration.calibration_node.logger", autospec=True)
    def test_execute_notebook_warnings_more_than_one_output(self, mocked_logger, mocked_pm_exec, output, methods_node):
        """Testing when no outputs or more than one outputs are received from ``execute_notebook()``."""
        methods_node._stream.getvalue.return_value = output  # type: ignore[attr-defined]

        methods_node._execute_notebook(methods_node.nb_path, "", {})

        mocked_logger.warning.assert_called_with(
            "If you had multiple outputs exported in %s, the last one found will be used.",
            methods_node.nb_path,
        )

        mocked_pm_exec.assert_called_once_with(
            methods_node.nb_path, "", {}, log_output=True, stdout_file=methods_node._stream
        )

    ##########################################
    # TEST CREATE NOTEBOOK DATETIME PATH ###
    ##########################################
    @pytest.mark.parametrize(
        "timestamp, dirty, error",
        [(None, True, True), (145783952598, False, True), (145783959532, False, False), (None, True, False)],
    )
    def test_create_notebook_datetime_path(
        self,
        timestamp,
        dirty,
        error,
        methods_node: CalibrationNode,
    ):
        """Test ``that create_notebook_datetime_path()`` works correctly."""
        with patch("qililab.calibration.calibration_node.os") as mocked_os:
            test_value = methods_node._create_notebook_datetime_path(timestamp=timestamp, dirty=dirty, error=error)
            mocked_os.makedirs.assert_called()
            if timestamp is not None:
                test_timestamp = datetime.fromtimestamp(timestamp)
                test_daily_path = f"{test_timestamp.year}_{test_timestamp.month:02d}_{test_timestamp.day:02d}"
                test_path = (
                    f"{test_daily_path}-"
                    + f"{test_timestamp.hour:02d}:{test_timestamp.minute:02d}:{test_timestamp.second:02d}"
                )
                # TODO: Solve this assert:
                # assert os.path.join(methods_node.nb_path, methods_node.node_id) in test_value
                assert f"_{test_path}" in test_value
            if dirty and not error:
                path_and_node_id = os.path.join(methods_node.nb_folder, methods_node.node_id)
                assert path_and_node_id in test_value
                assert "_dirty.ipynb" in test_value
            if error:
                path_and_node_id_error = os.path.join(methods_node.nb_folder, methods_node.node_id)
                assert path_and_node_id_error in test_value
                assert "_error.ipynb" in test_value

    ####################################
    # TEST PATH TO NAME AND FOLDER ###
    ####################################
    @pytest.mark.parametrize(
        "qubit, node_distinguisher, original_path, expected",
        [
            (0, 1, "foo/bar/foobar.ipynb", ("foobar_1_q0", "foo/bar")),
            ([0, 1], "long", "this/is/a/long/path/to/notebook.ipynb", ("notebook_long_q0q1", "this/is/a/long/path/to")),
        ],
    )
    def test_path_to_name_and_folder(
        self, methods_node: CalibrationNode, qubit, node_distinguisher, original_path, expected
    ):
        """Test that ``path_to_name_and_folder()`` works properly."""
        methods_node.qubit_index = qubit
        methods_node.node_distinguisher = node_distinguisher
        test_values = methods_node._path_to_name_and_folder(original_path)
        assert len(test_values) == 2
        assert test_values[0] == expected[0]
        assert test_values[1] == expected[1]

    ###########################################
    # TEST FIND LAST EXECUTED CALIBRATION ###
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
            f = open(os.path.join(methods_node.nb_folder, test_filename), "w")
            f.close()
        f = open(os.path.join(methods_node.nb_folder, filename_expected), "w")
        f.close()

        test_filename = methods_node._find_last_executed_calibration()

        assert filename_expected == test_filename

        for test_filename in test_filenames:
            os.remove(os.path.join(methods_node.nb_folder, test_filename))
        os.remove(os.path.join(methods_node.nb_folder, filename_expected))

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
            f = open(os.path.join(methods_node.nb_folder, test_filename), "w")
            f.close()

        test_filename = methods_node._find_last_executed_calibration()

        assert test_filename is None

        for test_filename in test_filenames:
            os.remove(os.path.join(methods_node.nb_folder, test_filename))

    ##########################################
    # TEST ADD STRING TO CHECKED NB NAME ###
    ##########################################
    def test_add_string_to_checked_nb_name(self, methods_node: CalibrationNode):
        """Test that ``add_string_to_checked_nb_name()`` works properly."""
        with patch("qililab.calibration.calibration_node.os.rename") as mocked_rename:
            timestamp_path = methods_node._create_notebook_datetime_path(timestamp=0).split(".ipynb")[0]
            string_to_add = "test_succesful"
            methods_node._add_string_to_checked_nb_name(string_to_add, timestamp=0)
            mocked_rename.assert_called_once_with(f"{timestamp_path}.ipynb", f"{timestamp_path}_{string_to_add}.ipynb")


class TestStaticMethodsFromCalibrationNode:
    """Test static methods of the `CalibrationNode` class."""

    ##########################################
    # TEST BUILD NOTEBOOKS LOGGER STREAM ###
    ##########################################
    @patch("qililab.calibration.calibration_node.logging", autospec=True)
    def test_build_notebooks_logger_stream(self, mocked_logging):
        """Test that ``build_notebooks_logger_stream()`` works properly."""
        stream = CalibrationNode._build_notebooks_logger_stream()
        mocked_logging.basicConfig.assert_called_once()
        assert isinstance(stream, StringIO)


#################################################################################
# TESTS FOR THE EXTERNAL FUNCTIONS #######################
#################################################################################


#######################################
# TEST EXPORT CALIBRATION OUTPUTS ###
#######################################
@pytest.mark.parametrize(
    "test_outputs, test_serializable_outputs",
    [
        ({"this_is": "a_test_dict", "foo": [1, 2, 3, 4]}, {"this_is": "a_test_dict", "foo": [1, 2, 3, 4]}),
        (
            {"this_is": np.array([1, 2, 3, 4, 5]), "foo": {"bar": "jose", "pepe": (np.array([0]), np.array([0]), "a")}},
            {"this_is": [1, 2, 3, 4, 5], "foo": {"bar": "jose", "pepe": [[0], [0], "a"]}},
        ),
    ],
)
@patch("qililab.calibration.calibration_node.json.dumps", autospec=True)
def test_export_nb_outputs(mocked_dumps, test_outputs, test_serializable_outputs):
    """Test that ``export_nb_outputs()`` works properly."""
    mocked_dumps.return_value = test_serializable_outputs
    with patch("builtins.print") as mocked_print:
        export_nb_outputs(test_outputs)
        mocked_dumps.assert_called_with(test_serializable_outputs)
        mocked_print.assert_called_with(f"{logger_output_start}{test_serializable_outputs}")


#######################################
# TEST JSON SERIALIZE #########
#######################################
@pytest.mark.parametrize(
    "test_objects, expected_test_objects",
    [
        (
            [np.array([1, 2, 3, 4]), [np.array([1, 2, 3, 4]), [2 + 1j, np.complex128(2 + 1j)]]],
            [[1.0, 2.0, 3.0, 4.0], [[1.0, 2.0, 3.0, 4.0], [{"real": 2.0, "imag": 1.0}, {"real": 2.0, "imag": 1.0}]]],
        ),
        (
            [np.True_, [np.float64(12.9), np.void(5)]],
            [True, [12.9, None]],
        ),
        (
            {"this_is": "a_test_dict", "foo": np.array([1, 2, 3, 4])},
            {"this_is": "a_test_dict", "foo": [1.0, 2.0, 3.0, 4.0]},
        ),
        (
            {"this_is": np.array([1, 2, 3, 4, 5]), "foo": {"bar": "jose", "pepe": (np.array([0]), np.array([0]), "a")}},
            {"this_is": [1.0, 2.0, 3.0, 4.0, 5.0], "foo": {"bar": "jose", "pepe": [[0], [0], "a"]}},
        ),
        (123, 123.0),
        (
            (np.array([1, 2, 3, 4, 5.5]), {"foo": np.array([0.1, 0.2, 0.3])}),
            [[1.0, 2.0, 3.0, 4.0, 5.5], {"foo": [0.1, 0.2, 0.3]}],
        ),
        (np.array([20, 30, 40]), [20.0, 30.0, 40.0]),
        ("qililab rocks!", "qililab rocks!"),
    ],
)
def test_json_serialize(test_objects, expected_test_objects):
    """Test that ``json_serialize()`` works properly."""
    test_result = _json_serialize(test_objects)
    assert test_result == expected_test_objects
