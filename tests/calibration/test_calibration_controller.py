from datetime import datetime
from unittest.mock import MagicMock, call, patch

import networkx as nx
import pandas as pd
import pytest

from qililab import Parameter
from qililab.calibration import CalibrationController, CalibrationNode
from qililab.data_management import build_platform
from qililab.platform.platform import Platform

# flake8: noqa


#################################################################################
#################################### SET UPS ####################################
#################################################################################

path_runcard = "tests/calibration/galadriel.yml"


def dummy_comparison_model(obtained: dict, comparison: dict) -> float:
    """Basic comparison model for testing."""
    return abs(sum(obtained["y"]) - sum(comparison["y"]))


######################
### NODES CREATION ###
######################
zeroth = CalibrationNode(
    nb_path="tests/calibration/notebook_test/zeroth.ipynb",
    qubit_index=[0, 1],  # qubit_index as list
)
first = CalibrationNode(
    nb_path="tests/calibration/notebook_test/first.ipynb",
    qubit_index=0,
)
second = CalibrationNode(
    nb_path="tests/calibration/notebook_test/second.ipynb",
    qubit_index=0,
)
third = CalibrationNode(
    nb_path="tests/calibration/notebook_test/third.ipynb",
    qubit_index=0,
)
fourth = CalibrationNode(
    nb_path="tests/calibration/notebook_test/fourth.ipynb",
    # no qubit index
)

# NODE MAPPING TO THE GRAPH (key = name in graph, value = node object):
nodes = {"zeroth_q0q1": zeroth, "first_q0": first, "second_q0": second, "third_q0": third, "fourth": fourth}


#######################
### GRAPHS CREATION ###
#######################

# fmt: off
# GOOD GRAPH CREATION:
G0 = nx.DiGraph()                           #        3 -->\
G0.add_edge("third_q0", "fourth")           #              \
G0.add_edge("second_q0", "fourth")          # 0 ---> 2 ---> 4
G0.add_edge("zeroth_q0q1", "second_q0")     #  \
G0.add_edge( "zeroth_q0q1", "first_q0")     #   \--> 1

# GOOD GRAPH CREATION:
G1 = nx.DiGraph()                           #        3 -->\
G1.add_edge("third_q0", "fourth")           #        ^     \
G1.add_edge("second_q0", "fourth")          # 0 ---> 2 ---> 4
G1.add_edge("zeroth_q0q1", "second_q0")     #  \     ^
G1.add_edge("zeroth_q0q1", "first_q0")      #   \--> 1
G1.add_edge("second_q0", "third_q0")
G1.add_edge("first_q0", "second_q0")

# GOOD GRAPH CREATION:
G2 = nx.DiGraph()                           #   /--> 3 ---> 4
G2.add_edge("third_q0", "fourth")           #  /
G2.add_edge("zeroth_q0q1", "third_q0")      # 0 ---> 2
G2.add_edge("zeroth_q0q1", "second_q0")     #  \
G2.add_edge("zeroth_q0q1", "first_q0")      #   \--> 1

# GOOD GRAPH CREATION:
G3 = nx.DiGraph()
G3.add_edge("third_q0", "fourth")           #   /--> 3 ---> 4
G3.add_edge("zeroth_q0q1", "third_q0")      #  /     ^
G3.add_edge("second_q0", "third_q0")        # 0 ---> 2
G3.add_edge("zeroth_q0q1", "second_q0")     #  \
G3.add_edge("zeroth_q0q1", "first_q0")      #   \--> 1

# GOOD GRAPH CREATION:
G4 = nx.DiGraph()
G4.add_edge("third_q0", "fourth")           #   /--> 2 -->\
G4.add_edge("second_q0", "third_q0")        #  /           \
G4.add_edge("first_q0", "third_q0")         # 0             3 ---> 4
G4.add_edge("zeroth_q0q1", "second_q0")     #  \           /
G4.add_edge("zeroth_q0q1", "first_q0")      #   \--> 1 -->/

# GOOD GRAPH CREATION:
G5 = nx.DiGraph()
G5.add_edge("third_q0", "fourth")           #   /--> 2 -->\
G5.add_edge("second_q0", "third_q0")        #  /     ^     \
G5.add_edge("first_q0", "third_q0")         # 0      |      3 ---> 4
G5.add_edge("zeroth_q0q1", "second_q0")     #  \     |     /
G5.add_edge("first_q0", "second_q0")        #   \--> 1 -->/
G5.add_edge("zeroth_q0q1", "first_q0")

# GOOD GRAPH CREATION:
G6 = nx.DiGraph()
G6.add_edge("third_q0", "fourth")           #   /--> 3 -->\
G6.add_edge("second_q0", "third_q0")        #  /     ^     \
G6.add_edge("zeroth_q0q1", "third_q0")      # 0 ---> 2      4
G6.add_edge("zeroth_q0q1", "second_q0")     #  \     v     /
G6.add_edge("second_q0", "first_q0")        #   \--> 1 -->/
G6.add_edge("zeroth_q0q1", "first_q0")
G6.add_edge("first_q0", "fourth")

# GOOD GRAPH CREATION:
G7 = nx.DiGraph()
G7.add_edge("third_q0", "fourth")           #   /--> 3 -->\
G7.add_edge("second_q0", "third_q0")        #  /     ^     \
G7.add_edge("zeroth_q0q1", "third_q0")      # 0 ---> 2      4
G7.add_edge("zeroth_q0q1", "second_q0")     #  \     ^     /
G7.add_edge("first_q0", "second_q0")        #   \--> 1 -->/
G7.add_edge("zeroth_q0q1", "first_q0")
G7.add_edge("first_q0", "fourth")

# GOOD GRAPH CREATION:
G8 = nx.DiGraph()
G8.add_edge("third_q0", "fourth")           #   /--> 3 -->\
G8.add_edge("second_q0", "third_q0")        #  /     ^     \
G8.add_edge("zeroth_q0q1", "third_q0")      # 0 ---> 2 ---> 4
G8.add_edge("zeroth_q0q1", "second_q0")     #  \     v     /
G8.add_edge("second_q0", "first_q0")        #   \--> 1 -->/
G8.add_edge("zeroth_q0q1", "first_q0")
G8.add_edge("second_q0", "fourth")
G8.add_edge("first_q0", "fourth")

# GOOD GRAPH CREATION:                      #        |
G9 = nx.DiGraph()                           #        v
G9.add_edge("third_q0", "fourth")           #   /--> 3 -->\
G9.add_edge("second_q0", "third_q0")        #  /     ^     \
G9.add_edge("zeroth_q0q1", "third_q0")      # 0 ---> 2 ---> 4
G9.add_edge("zeroth_q0q1", "second_q0")     #  \     v     /
G9.add_edge("second_q0", "first_q0")        #   \--> 1 -->/
G9.add_edge("zeroth_q0q1", "first_q0")      #        |
G9.add_edge("second_q0", "fourth")          #        v
G9.add_edge("first_q0", "fourth")
G9.add_edge("first_q0", "third_q0")

# BAD GRAPH CREATION:
B = nx.DiGraph()                            #         /---<---\
B.add_edge("third_q0", "fourth")            #        /         \
B.add_edge("second_q0", "third_q0")         # 0 --> 1 --> 2 --> 3 --> 4
B.add_edge("first_q0", "second_q0")
B.add_edge("zeroth_q0q1", "first_q0")
B.add_edge("third_q0", "first_q0")

good_graphs = [G0, G1, G2, G3, G4, G5, G6, G7, G8, G9]

# Leaves to Roots recursive calls of each graph. Examples: Calibrate and update_param.
G0_calls = [call(third), call(zeroth), call(second), call(fourth)]
G1_calls = [call(zeroth), call(first), call(second), call(third), call(fourth)]
G2_calls = [call(zeroth), call(third), call(fourth)]
G3_calls = [call(zeroth), call(second), call(third), call(fourth)]
G4_calls = [call(zeroth), call(second), call(first), call(third), call(fourth)]
G5_calls = [call(zeroth), call(first), call(second), call(third), call(fourth)]
G6_calls = [call(zeroth), call(second), call(third), call(first), call(fourth)]
G7_calls = [call(zeroth), call(first), call(second), call(third), call(fourth)]
G8_calls = [call(zeroth), call(second), call(third), call(first), call(fourth)]
G9_calls = [call(zeroth), call(second), call(first), call(third), call(fourth)]

leaves_to_roots_good_graphs_calls = [G0_calls,G1_calls ,G2_calls,G3_calls,G4_calls,G5_calls,G6_calls,G7_calls,G8_calls,G9_calls]
# fmt: on


##########################
### MOCKED CONTROLLERS ###
##########################
class RunAutomaticCalibrationMockedController(CalibrationController):
    """``CalibrationController`` to test the workflow of ``run_automatic_calibration()``, where its mocked ``calibrate_all()``, ``get_last_set_parameters()`` and ``get_last_fidelities()``."""

    def __init__(self, node_sequence, calibration_graph, runcard):
        super().__init__(node_sequence=node_sequence, calibration_graph=calibration_graph, runcard=runcard)
        self.calibrate_all = MagicMock(return_value=None)
        self.get_qubits_tables = MagicMock(return_value=(10, 10))
        self.get_last_set_parameters = MagicMock(
            return_value={("test", "test"): (0.0, "test", datetime.fromtimestamp(1999))}
        )
        self.get_last_fidelities = MagicMock(return_value={"test": (0.0, "test", datetime.fromtimestamp(1999))})


class CalibrateAllMockedController(CalibrationController):
    """``CalibrationController`` to test the workflow of ``calibrate_all()`` where its mocked ``calibrate()`` and ``update_parameters()``."""

    def __init__(self, node_sequence, calibration_graph, runcard):
        super().__init__(node_sequence=node_sequence, calibration_graph=calibration_graph, runcard=runcard)
        self.calibrate = MagicMock(return_value=None)
        self._update_parameters = MagicMock(return_value=None)


#################################################################################
############################## TESTS FOR THE CLASS ##############################
#################################################################################


###########################
### TEST INITIALIZATION ###
###########################
class TestInitializationCalibrationController:
    """Unit tests for the CalibrationController class initialization."""

    @pytest.mark.parametrize(
        "controller",
        [
            (graph, CalibrationController(node_sequence=nodes, calibration_graph=graph, runcard=path_runcard))
            for graph in good_graphs
        ],
    )
    def test_good_init_method(self, controller):
        """Test a valid initialization of the class."""
        # Assert:
        assert controller[1].calibration_graph == controller[0]
        assert isinstance(controller[1].calibration_graph, nx.DiGraph)
        assert controller[1].node_sequence == nodes
        assert isinstance(controller[1].node_sequence, dict)
        assert controller[1].runcard == path_runcard
        assert isinstance(controller[1].runcard, str)
        assert controller[1].platform.to_dict() == build_platform(path_runcard).to_dict()
        assert isinstance(controller[1].platform, Platform)
        assert controller[1].drift_timeout == 7200

    def test_bad_init_method(self):
        """Test an invalid initialization of the class.

        This happens when the graph is not a Direct Acyclic Graph.
        """
        # Assert:
        with pytest.raises(ValueError) as error:
            _ = CalibrationController(node_sequence=nodes, calibration_graph=B, runcard=path_runcard)

        assert str(error.value) == "The calibration graph must be a Directed Acyclic Graph (DAG)."


######################################
### TEST RUN AUTOMATIC CALIBRATION ###
######################################
@pytest.mark.parametrize(
    "controller",
    [
        RunAutomaticCalibrationMockedController(node_sequence=nodes, calibration_graph=graph, runcard=path_runcard)
        for graph in good_graphs
    ],
)
class TestRunAutomaticCalibrationFromCalibrationController:
    """Test that ``run_autoamtic_calibration()`` of ``CalibrationController`` behaves well."""

    def test_run_automatic_calibration(self, controller):
        """Test that `run_automatic_calibration()` gets the proper nodes to calibrate_all()."""
        # Act:
        output_dict = controller.run_automatic_calibration()

        # Asserts:
        controller.get_last_set_parameters.assert_called_once_with()
        controller.get_last_fidelities.assert_called_once_with()
        controller.get_qubits_tables.assert_called_once_with()

        assert output_dict == {
            "1q_table": 10,
            "2q_table": 10,
            "set_parameters": {("test", "test"): (0.0, "test", datetime.fromtimestamp(1999))},
            "fidelities": {"test": (0.0, "test", datetime.fromtimestamp(1999))},
        }

        # sourcery skip: extract-duplicate-method
        if controller.calibration_graph in [G0, G3]:
            controller.calibrate_all.assert_any_call(fourth)
            controller.calibrate_all.assert_any_call(first)
            assert controller.calibrate_all.call_count == 2

        elif controller.calibration_graph == G2:
            controller.calibrate_all.assert_any_call(fourth)
            controller.calibrate_all.assert_any_call(second)
            controller.calibrate_all.assert_any_call(first)
            assert controller.calibrate_all.call_count == 3

        elif controller.calibration_graph in [G1, G4, G5, G6, G7, G8, G9]:
            controller.calibrate_all.assert_any_call(fourth)
            assert controller.calibrate_all.call_count == 1


##########################
### TEST CALIBRATE ALL ###
##########################
@pytest.mark.parametrize(
    "controller",
    [
        (
            graph,
            expected_call_order,
            CalibrateAllMockedController(node_sequence=nodes, calibration_graph=graph, runcard=path_runcard),
        )
        for graph, expected_call_order in zip(good_graphs, leaves_to_roots_good_graphs_calls)
    ],
)
class TestCalibrateAllFromCalibrationController:
    """Test that ``calibrate_all()`` of ``CalibrationConroller`` behaves well."""

    def test_low_level_mockings_working_properly(self, controller):
        """Test that the mockings are working properly."""
        # Assert:
        assert all(node.previous_timestamp is None for node in controller[2].node_sequence.values())
        assert controller[2].calibrate() is None
        assert controller[2]._update_parameters() is None

    def test_calls_for_linear_calibration(self, controller):
        """Test that ``calibrate_all`` follows the correct logic for each graph, from leaves up to the roots"""

        # Reset mock calls:
        controller[2].calibrate.reset_mock()
        controller[2]._update_parameters.reset_mock()
        for node in controller[2].node_sequence.values():
            node.been_calibrated = False

        # Act:
        controller[2].calibrate_all(fourth)

        # Assert that 0, 3 & 4 notebooks have been calibrated:
        # (1 and 2 are calibrated in some graphs and not in others)
        for node in [zeroth, third, fourth]:
            assert node.been_calibrated is True

        # Asserts recursive calls
        controller[2].calibrate.assert_has_calls(controller[1])
        controller[2]._update_parameters.assert_has_calls(controller[1])


@pytest.mark.parametrize(
    "controller",
    [
        CalibrationController(node_sequence=nodes, calibration_graph=graph, runcard=path_runcard)
        for graph in good_graphs
    ],
)
class TestCalibrationController:
    """Test that the rest of ``CalibrationController`` methods behave well."""

    ######################
    ### TEST CALIBRATE ###
    ######################
    @patch("qililab.calibration.calibration_node.CalibrationNode.run_node")
    @patch("qililab.calibration.calibration_node.CalibrationNode._add_string_to_checked_nb_name")
    def test_calibrate(self, mock_add_str, mock_run, controller):
        """Test that the calibration method, calls node.run_node()."""
        for node in controller.node_sequence.values():
            controller.calibrate(node)
        assert mock_run.call_count == len(controller.node_sequence)
        assert mock_add_str.call_count == len(controller.node_sequence)

    ##############################
    ### TEST UPDATE PARAMETERS ###
    ##############################

    @patch("qililab.platform.Platform.set_parameter")
    @patch("qililab.calibration.calibration_controller.save_platform")
    def test_update_parameters(self, mock_save_platform, mock_set_params, controller):
        """Test that the update parameters method, calls ``platform.set_parameter()`` and ``save_platform()``."""
        for node in controller.node_sequence.values():
            node.output_parameters = {
                "platform_parameters": [
                    (Parameter.AMPLITUDE, 0, "test_bus", node.qubit_index),
                    (Parameter.AMPLITUDE, 1, "test_bus2", node.qubit_index),
                ]
            }
            controller._update_parameters(node)

            mock_set_params.assert_called_with(
                parameter=Parameter.AMPLITUDE, value=1, alias="test_bus2", channel_id=node.qubit_index
            )  # Checking the last call of the 2 there are.
            mock_save_platform.assert_called_with(controller.runcard, controller.platform)  # Checking the save call

        assert mock_set_params.call_count == 2 * len(controller.node_sequence)
        assert mock_save_platform.call_count == len(controller.node_sequence)

    ####################################
    ### TEST GET LAST SET PARAMETERS ###
    ####################################
    def test_get_last_set_parameters(self, controller):
        """Test that the ``get_last_set_parameters()`` method, gets the correct parameters."""
        for i, node in controller.node_sequence.items():
            node.output_parameters = {
                "platform_parameters": [("param", 0, f"test_bus_{i}", 0), ("param", 1, f"test_bus_{i}", 1)],
                "fidelities": [(0, f"param_{i}", 1), (1, f"param_{i}", 0.967)],
            }
            node.previous_timestamp = 1999

        df = controller.get_last_set_parameters()

        # Create the pandas DataFrame to test
        data = [
            [0, "zeroth_q0q1", datetime.fromtimestamp(1999)],
            [1, "zeroth_q0q1", datetime.fromtimestamp(1999)],
            [0, "first_q0", datetime.fromtimestamp(1999)],
            [1, "first_q0", datetime.fromtimestamp(1999)],
            [0, "second_q0", datetime.fromtimestamp(1999)],
            [1, "second_q0", datetime.fromtimestamp(1999)],
            [0, "third_q0", datetime.fromtimestamp(1999)],
            [1, "third_q0", datetime.fromtimestamp(1999)],
            [0, "fourth", datetime.fromtimestamp(1999)],
            [1, "fourth", datetime.fromtimestamp(1999)],
        ]
        idx = pd.MultiIndex.from_product(
            [
                ["param"],
                [
                    "test_bus_zeroth_q0q1",
                    "test_bus_first_q0",
                    "test_bus_second_q0",
                    "test_bus_third_q0",
                    "test_bus_fourth",
                ],
                [0, 1],
            ],
            names=["parameter", "bus", "qubit"],
        )
        col = ["value", "node_id", "datetime"]
        test_df = pd.DataFrame(data, idx, col)

        assert pd.testing.assert_frame_equal(df, test_df, check_dtype=False) is None

    ################################
    ### TEST GET LAST FIDELITIES ###
    ################################
    def test_get_last_fidelities(self, controller):
        """Test that the ``get_last_fidelities()`` method, gets the correct parameters."""
        for i, node in controller.node_sequence.items():
            node.output_parameters = {
                "platform_parameters": [(f"test_bus_{i}", 0, "param", 0), (f"test_bus_{i}", 1, "param", 1)],
                "fidelities": [(0, f"param_{i}", 1), (1, f"param_{i}", 0.967)],
            }
            node.previous_timestamp = 1999

        df = controller.get_last_fidelities()

        # Create the pandas DataFrame to test
        data = [
            [1, "zeroth_q0q1", datetime.fromtimestamp(1999)],
            [0.967, "zeroth_q0q1", datetime.fromtimestamp(1999)],
            [1, "first_q0", datetime.fromtimestamp(1999)],
            [0.967, "first_q0", datetime.fromtimestamp(1999)],
            [1, "second_q0", datetime.fromtimestamp(1999)],
            [0.967, "second_q0", datetime.fromtimestamp(1999)],
            [1, "third_q0", datetime.fromtimestamp(1999)],
            [0.967, "third_q0", datetime.fromtimestamp(1999)],
            [1, "fourth", datetime.fromtimestamp(1999)],
            [0.967, "fourth", datetime.fromtimestamp(1999)],
        ]
        idx = pd.MultiIndex.from_product(
            [
                [
                    "param_zeroth_q0q1",
                    "param_first_q0",
                    "param_second_q0",
                    "param_third_q0",
                    "param_fourth",
                ],
                [0, 1],
            ],
            names=["fidelity", "qubit"],
        )
        col = ["fidelity", "node_id", "datetime"]
        test_df = pd.DataFrame(data, idx, col)

        assert pd.testing.assert_frame_equal(df, test_df, check_dtype=False) is None

    ################################
    ##### TEST GET QUBITS TABLE ####
    ################################
    def test_get_qubits_table_and_test_create_empty_dataframe(self, controller):
        """Test that the ``get_qubits_table()`` and ``_create_empty_dataframes()`` methods, gets the correct structure and parameters."""
        for ind, (_, node) in enumerate(controller.node_sequence.items()):
            if node.node_id == "zeroth_q0q1":
                node.output_parameters = {
                    "platform_parameters": [(f"param_{ind}", 1, "test_bus", "0-1")],
                    "fidelities": [("0-1", f"fidelity_{ind}", 0.967)],
                }

            elif node.node_id == "fourth":
                node.node_id = "fourth_q1"
                node.output_parameters = {
                    "platform_parameters": [(f"param_{ind}", 1, "test_bus", 1)],
                    "fidelities": [(1, f"fidelity_{ind}", 0.967)],
                }

            else:
                node.output_parameters = {
                    "platform_parameters": [(f"param_{ind}", 1, "test_bus", 0)],
                    "fidelities": [(0, f"fidelity_{ind}", 0.967)],
                }
            node.previous_timestamp = 1999

        # Generate the empty dataframes, and the filled ones, for testing both functions.
        empty_q1_df, empty_q2_df = controller._create_empty_dataframes()
        q1_df, q2_df = controller.get_qubits_tables()

        # Create the pandas DataFrames idx, columns and data to test:
        idx = ["0-1", "0", "1"]
        data = [
            [1, 0.967],
            [1, 1, 1, "-", 0.967, 0.967, 0.967, "-"],
            ["-", "-", "-", 1, "-", "-", "-", 0.967],
        ]
        empty_data = [
            ["-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
        ]
        col_q1 = [
            "param_1_test_bus",
            "param_2_test_bus",
            "param_3_test_bus",
            "param_4_test_bus",
            "fidelity_1",
            "fidelity_2",
            "fidelity_3",
            "fidelity_4",
        ]
        col_q2 = [
            "param_0_test_bus",
            "fidelity_0",
        ]

        # Create the check empty dataframes:
        test_empty_q1_df = pd.DataFrame(empty_data[1:], idx[1:], col_q1)
        test_empty_q2_df = pd.DataFrame(empty_data[:1], idx[:1], col_q2)

        # Create the check filled dataframes:
        test_q1_df = pd.DataFrame(data[1:], idx[1:], col_q1)
        test_q2_df = pd.DataFrame(data[:1], idx[:1], col_q2)

        # Give name to the index to the test dataframes:
        for df in [test_q1_df, test_q2_df, test_empty_q1_df, test_empty_q2_df]:
            df.index.name = "qubit"

        # Testing the empty dataframes structure:
        assert (
            pd.testing.assert_frame_equal(
                empty_q1_df,
                test_empty_q1_df,
                check_dtype=False,
                check_like=True,
                check_index_type=False,
                check_column_type=False,
            )
            is None
        )
        assert (
            pd.testing.assert_frame_equal(
                empty_q2_df,
                test_empty_q2_df,
                check_dtype=False,
                check_like=True,
                check_index_type=False,
                check_column_type=False,
            )
            is None
        )

        # Testing that the dataframes got filled correctly
        assert (
            pd.testing.assert_frame_equal(
                q1_df, test_q1_df, check_dtype=False, check_like=True, check_index_type=False, check_column_type=False
            )
            is None
        )
        assert (
            pd.testing.assert_frame_equal(
                q2_df, test_q2_df, check_dtype=False, check_like=True, check_index_type=False, check_column_type=False
            )
            is None
        )

        # Undo the previous change to the node_id, for the nexts tests:
        for node in controller.node_sequence.values():
            if node.node_id == "fourth_q1":
                node.node_id = "fourth"

    def test_reorder_fidelities(self, controller):
        """Test that the reorder method, puts the fidelities in the front."""
        idx = ["0", "1"]

        empty_data = [
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
        ]
        col = [
            "param_1_test_bus",
            "param_2_test_bus",
            "param_3_test_bus",
            "param_4_test_bus",
            "fidelity_1",
            "fidelity_2",
            "fidelity_3",
            "fidelity_4",
        ]

        reordered_col = [
            "fidelity_4",
            "fidelity_3",
            "fidelity_2",
            "fidelity_1",
            "param_1_test_bus",
            "param_2_test_bus",
            "param_3_test_bus",
            "param_4_test_bus",
        ]

        df = pd.DataFrame(empty_data, idx, col)
        df = controller._reorder_fidelities(df)

        ordered_df = pd.DataFrame(empty_data, idx, reordered_col)

        assert pd.testing.assert_frame_equal(df, ordered_df, check_dtype=False, check_index_type=False) is None

    #########################
    ### TEST DEPENDENCIES ###
    #########################
    def test_dependencies(self, controller):
        """Test that dependencies return the correct dependencies."""
        result = controller._dependencies(nodes["zeroth_q0q1"])
        assert result == []

        result = controller._dependencies(nodes["fourth"])
        if controller.calibration_graph in [G0, G1]:
            assert third in result and second in result
            assert len(result) == 2

        elif controller.calibration_graph in [G2, G3, G4, G5]:
            assert third in result
            assert len(result) == 1

        elif controller.calibration_graph in [G6, G7]:
            assert third in result and first in result
            assert len(result) == 2

        elif controller.calibration_graph in [G8, G9]:
            assert third in result and second in result and first in result
            assert len(result) == 3

    def test_get_qubit_from_node(self, controller):
        """Test that the method ``get_qubit_from_node()`` returns the correct qubit index."""
        for node in controller.node_sequence.values():
            if isinstance(node.qubit_index, int):
                assert controller._get_qubit_from_node(node) == str(node.qubit_index)
            elif isinstance(node.qubit_index, list):
                assert controller._get_qubit_from_node(node) == "-".join(map(str, node.qubit_index))

    def test_get_bus_name_from_alias(self, controller):
        """Test that the method ``get_bus_name_from_alias()`` returns the correct bus name."""
        assert controller._get_bus_name_from_alias("test_bus_h56_gt") == "test_bus_gt"




class TestStaticMethodsFromCalibrationController:
    """Test that the static methods of ``CalibrationController`` behave well."""

    ###############################
    ### TEST IS TIMEOUT EXPIRED ###
    ###############################
    @pytest.mark.parametrize(
        "timestamp",
        [datetime(2023, 1, 1).timestamp(), datetime.now().timestamp() - 3600, datetime.now().timestamp() - 3600 * 23],
        ids=["timestampA", "timestampB", "timestampC"],
    )
    def test_timeout_expired(self, timestamp):
        """Tests cases where timeout should be expired."""
        timeout = 1800
        assert CalibrationController._is_timeout_expired(timestamp, timeout) is True

    @pytest.mark.parametrize(
        "timestamp",
        [datetime.now().timestamp(), datetime.now().timestamp() - 1700],
        ids=["timestampA", "timestampB"],
    )
    def test_timeout_not_expired(self, timestamp):
        """Test cases where timeout should not be expired."""
        timeout = 1800
        assert CalibrationController._is_timeout_expired(timestamp, timeout) is False
