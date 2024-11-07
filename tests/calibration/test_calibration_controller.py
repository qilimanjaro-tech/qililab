# mypy: disable-error-code = "attr-defined, func-returns-value, call-arg"
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

##################################
### CHECKPOINTS NODES CREATION ###
##################################
first_checkpoint = CalibrationNode(
    nb_path="tests/calibration/notebook_test/first.ipynb",
    node_distinguisher="cp",
    qubit_index=0,
    checkpoint=True,
    check_value={"fidelity_first": 0.5},
)
first_checkpoint.previous_timestamp = datetime.now().timestamp()-7200.0
# Making the first checkpoint pass!
first_checkpoint.output_parameters = {"fidelities": {"fidelity_first": 0.6}}

second_checkpoint = CalibrationNode(
    nb_path="tests/calibration/notebook_test/second.ipynb",
    node_distinguisher="cp",
    qubit_index=0,
    checkpoint=True,
    check_value={"fidelity_second": 0.5},
)
second_checkpoint.previous_timestamp = datetime.now().timestamp()-7200.0

# ADDING CHECKPOINTS TO THE NODES MAPPING:
nodes_w_cp = nodes | {"first_cp_q0": first_checkpoint, "second_cp_q0": second_checkpoint}

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

# CHECKPOINTS GRAPH CREATION:
CP_1 = nx.DiGraph()                            #   /--> 1   /--> 2 -->\
CP_1.add_edge("zeroth_q0q1", "first_q0")       #  /        /           \
CP_1.add_edge("zeroth_q0q1", "first_cp_q0")    # 0 --> CP_1             CP_2 --> 4
CP_1.add_edge("first_cp_q0", "second_q0")      #           \           /
CP_1.add_edge("first_cp_q0", "third_q0")       #            \--> 3 -->/
CP_1.add_edge("second_q0", "second_cp_q0")
CP_1.add_edge("third_q0", "second_cp_q0")
CP_1.add_edge("second_cp_q0", "fourth")

# CHECKPOINTS GRAPH CREATION:
CP_2 = nx.DiGraph()                            #   /--> 1 -->\
CP_2.add_edge("zeroth_q0q1", "first_q0")       #  /           \
CP_2.add_edge("zeroth_q0q1", "second_q0")      # 0 ---> 2 ---> CP_1 --> CP_2 --> 4
CP_2.add_edge("first_q0", "first_cp_q0")       #         \              /
CP_2.add_edge("second_q0", "first_cp_q0")      #          \---> 3 ---> /
CP_2.add_edge("second_q0", "third_q0")
CP_2.add_edge("first_cp_q0", "second_cp_q0")
CP_2.add_edge("third_q0", "second_cp_q0")
CP_2.add_edge("second_cp_q0", "fourth")


# List of graphs:
good_graphs = [G0, G1, G2, G3, G4, G5, G6, G7, G8, G9]
checkpoints_graphs = [CP_1, CP_2]

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

# For diagnosing, if no passed checkpoint, we only need to go through one path, so we reverse the calls:
CP_1_diagnose_no_V_calls = ['fourth', 'second_cp_q0', 'second_q0', 'first_cp_q0', 'zeroth_q0q1', 'third_q0', 'first_cp_q0', 'zeroth_q0q1']
CP_2_diagnose_no_V_calls = ['fourth', 'second_cp_q0', 'first_cp_q0', 'first_q0', 'zeroth_q0q1', 'second_q0', 'zeroth_q0q1', 'third_q0', 'second_q0', 'zeroth_q0q1']

checkpoints_diagnose_no_V_calls = [CP_1_diagnose_no_V_calls, CP_2_diagnose_no_V_calls]
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
        self.diagnose_checkpoint = MagicMock(return_value=None)
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
        "graph, controller",
        [
            (graph, CalibrationController(node_sequence=nodes, calibration_graph=graph, runcard=path_runcard))
            for graph in good_graphs
        ],
    )
    def test_good_init_method(self, graph, controller: CalibrationController):
        """Test a valid initialization of the class."""
        # Assert:
        assert controller.calibration_graph == graph
        assert isinstance(controller.calibration_graph, nx.DiGraph)
        assert controller.node_sequence == nodes
        assert isinstance(controller.node_sequence, dict)
        assert controller.runcard == path_runcard
        assert isinstance(controller.runcard, str)
        assert controller.platform.to_dict() == build_platform(path_runcard).to_dict()
        assert isinstance(controller.platform, Platform)
        assert controller.drift_timeout == 7200

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

    def test_run_automatic_calibration(self, controller: RunAutomaticCalibrationMockedController):
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
            controller.calibrate_all.assert_has_calls([call(fourth), call(first)])
            controller.diagnose_checkpoint.assert_has_calls([call(fourth), call(first)])
            assert controller.calibrate_all.call_count == 2
            assert controller.diagnose_checkpoint.call_count == 2

        elif controller.calibration_graph == G2:
            controller.calibrate_all.assert_has_calls([call(fourth), call(second), call(first)])
            controller.diagnose_checkpoint.assert_has_calls([call(fourth), call(second), call(first)])
            assert controller.calibrate_all.call_count == 3
            assert controller.diagnose_checkpoint.call_count == 3

        elif controller.calibration_graph in [G1, G4, G5, G6, G7, G8, G9]:
            controller.calibrate_all.assert_has_calls([call(fourth)])
            controller.diagnose_checkpoint.assert_has_calls([call(fourth)])
            assert controller.calibrate_all.call_count == 1
            assert controller.diagnose_checkpoint.call_count == 1

# TODO: Finish this:
#######################################################
### TEST RUN AUTOMATIC CALIBRATION WITH CHECKPOINTS ###
#######################################################
# @pytest.mark.parametrize(
#     "controller",
#     [
#         RunAutomaticCalibrationMockedController(node_sequence=nodes_w_cp, calibration_graph=graph, runcard=path_runcard)
#         for graph in checkpoints_graphs
#     ],
# )
# class TestRunAutomaticCalibrationWithCheckpointsFromCalibrationController:
#     """Test that ``run_autoamtic_calibration()`` of ``CalibrationController`` behaves well."""
#     def test_run_automatic_calibration_with_checkpoints(self, controller: RunAutomaticCalibrationMockedController):
#         """Test that `run_automatic_calibration()` gets the proper nodes to calibrate_all()."""

#         # Act:
#         output_dict = controller.run_automatic_calibration()

#         # Asserts:
#         controller.get_last_set_parameters.assert_called_once_with()
#         controller.get_last_fidelities.assert_called_once_with()
#         controller.get_qubits_tables.assert_called_once_with()

#         assert output_dict == {
#             "1q_table": 10,
#             "2q_table": 10,
#             "set_parameters": {("test", "test"): (0.0, "test", datetime.fromtimestamp(1999))},
#             "fidelities": {"test": (0.0, "test", datetime.fromtimestamp(1999))},
#         }

#         # controller.calibrate_all.assert_has_calls([call(fourth), call(first_checkpoint)])
#         # controller.diagnose_checkpoint.assert_has_calls([call(fourth), call(first_checkpoint)])
#         assert controller.calibrate_all.call_count == 2
#         assert controller.diagnose_checkpoint.call_count == 2

    # THIS GOES HERE:
        # # Looping for checkpoints passing or not: 0.6 means V, 0.4 means X
        # for (first_cp_fid, second_cp_fid), which_passed in zip([(0.6, 0.6), (0.6, 0.4), (0.4, None)], ["both_passed", "first_passed", "none_passed"]):

        #     # Setting if the checkpoints passed or not:
        #     first_checkpoint.output_parameters = {"fidelities": {"fidelity_first": first_cp_fid}}
        #     second_checkpoint.output_parameters = {"fidelities": {"fidelity_second": second_cp_fid}}



##########################
### TEST CALIBRATE ALL ###
##########################
@pytest.mark.parametrize(
    "controller, expected_calls",
    [
        (CalibrateAllMockedController(node_sequence=nodes, calibration_graph=graph, runcard=path_runcard), expected_call_order)
        for graph, expected_call_order in zip(good_graphs, leaves_to_roots_good_graphs_calls)
    ],
)
class TestCalibrateAllFromCalibrationController:
    """Test that ``calibrate_all()`` of ``CalibrationConroller`` behaves well."""

    def test_low_level_mockings_working_properly(self, controller: CalibrateAllMockedController, expected_calls: list):
        """Test that the mockings are working properly."""
        # Assert:
        assert all(node.previous_timestamp is None for node in controller.node_sequence.values())
        assert controller.calibrate() is None
        assert controller._update_parameters() is None

    def test_calibrate_all_calls_for_linear_calibration(self, controller: CalibrateAllMockedController, expected_calls: list):
        """Test that ``calibrate_all`` follows the correct logic for each graph, from leaves up to the roots"""

        # Reset mock calls:
        controller.calibrate.reset_mock()
        controller._update_parameters.reset_mock()
        for node in controller.node_sequence.values():
            node.been_calibrated_succesfully = False

        # Act:
        controller.calibrate_all(fourth)

        # Assert that 0, 3 & 4 notebooks have been calibrated:
        # (1 and 2 are calibrated in some graphs and not in others)
        for node in [zeroth, third, fourth]:
            assert node.been_calibrated_succesfully is True

        # Asserts recursive calls
        controller.calibrate.assert_has_calls(expected_calls)
        controller._update_parameters.assert_has_calls(expected_calls)

    def test_calibrate_all_with_checkpoint_passed(self, controller: CalibrateAllMockedController, expected_calls: list):
        """Test that ``calibrate_all`` follows the correct logic for a checkpoint passed."""

        # Reset mock calls:
        controller.calibrate.reset_mock()
        controller._update_parameters.reset_mock()

        # Set fourth as a checkpoint passed:
        controller.node_sequence["fourth"].checkpoint_passed = True

        # Act:
        controller.calibrate_all(fourth)

        # Assert no other method is called if fourth as checkpoint is passed:
        controller.calibrate.assert_not_called()
        controller._update_parameters.assert_not_called()


#################################
### TEST DIAGNOSE CHECKPOINTS ###
#################################
@pytest.mark.parametrize(
    "controller, calls",
    [
        (CalibrateAllMockedController(node_sequence=nodes_w_cp, calibration_graph=graph, runcard=path_runcard), calls)
        for graph, calls in zip(checkpoints_graphs, checkpoints_diagnose_no_V_calls)
    ],
)
class TestDiagnoseCheckpointsFromCalibrationController:
    """Test that ``diagnose_checkpoint()`` of ``CalibrationConroller`` behaves well."""

    def test_low_level_mockings_working_properly(self, controller: CalibrateAllMockedController, calls: list):
        """Test that the mockings are working properly."""
        assert controller.calibrate() is None
        assert controller._update_parameters() is None

    @patch("qililab.calibration.calibration_controller.logger.info")
    def test_calls_for_diagnosing_checkpoints(self, logger_mock, controller: CalibrateAllMockedController, calls: list):
        """Test that ``diagnose_checkpoint()`` follows the correct logic for each graph, from leaves up to the roots"""

        # Reset mock calls:
        controller.calibrate.reset_mock()
        controller._update_parameters.reset_mock()
        for node in controller.node_sequence.values():
            node.checkpoint_passed = None
            node.been_calibrated_succesfully = False

        # Act:
        controller.diagnose_checkpoint(fourth)

        # Assert first logger.info called, and assert its called to all dependencies
        logger_calls = [call("WORKFLOW: Diagnosing  %s.\n", string) for string in calls]

        # Adding the final calls, after first checkpoint passed and second failed:
        if controller.calibration_graph == CP_1:
            logger_calls.append(call('WORKFLOW: %s checkpoint already checked, skipping it.\n', 'first_cp_q0'))
        logger_calls.append(call('WORKFLOW: %s checkpoint failed, calibration will start just after the previously passed checkpoint.\n', 'second_cp_q0'))
        logger_mock.assert_has_calls(logger_calls)

        # Assert that no node has been marked as passed:
        for node in nodes.values():
            assert node.checkpoint_passed is None
            assert node.been_calibrated_succesfully is False

        # For the checkpoint that passed we got:
        assert nodes_w_cp["first_cp_q0"].checkpoint_passed is True
        assert nodes_w_cp["first_cp_q0"].been_calibrated_succesfully is True

        # For the checkpoint that failed we got:
        assert nodes_w_cp["second_cp_q0"].checkpoint_passed is False

        # Asserts calls for the checkpoints that passed and non, respectively:
        controller.calibrate.assert_has_calls([call(node) for node in [nodes_w_cp["first_cp_q0"], nodes_w_cp["second_cp_q0"]]])
        controller._update_parameters.assert_called_once_with(nodes_w_cp["first_cp_q0"])

@pytest.mark.parametrize(
    "controller",
    [
        CalibrateAllMockedController(node_sequence=nodes, calibration_graph=graph, runcard=path_runcard)
        for graph in good_graphs
    ],
)
class TestDiagnoseWithoutCheckpointsFromCalibrationController:
    """Test that ``diagnose_checkpoint()`` of ``CalibrationConroller`` behaves well."""

    def test_low_level_mockings_working_properly_without_checkpoints(self, controller: CalibrateAllMockedController):
        """Test that the mockings are working properly."""
        # Assert:
        assert all(node.previous_timestamp is None for node in controller.node_sequence.values())
        assert controller.calibrate() is None
        assert controller._update_parameters() is None

    @patch("qililab.calibration.calibration_controller.logger.info")
    def test_calls_for_diagnosing_without_checkpoints(self, logger_mock, controller: CalibrateAllMockedController):
        """Test that ``diagnose_checkpoint()`` follows the correct logic for each graph, from leaves up to the roots"""
        # Reset mock calls:
        controller.calibrate.reset_mock()
        controller._update_parameters.reset_mock()
        for node in controller.node_sequence.values():
            node.checkpoint_passed = None
            node.been_calibrated_succesfully = False

        # Act:
        controller.diagnose_checkpoint(fourth)

        # Assert first logger.info called, and assert its called to all dependencies
        for node_str in controller.node_sequence:
            # Graphs 0, 3 and 2, don't have all the branches finishing in "fourth", so first and second are not diagnosed always:
            if controller.calibration_graph in [G0, G3] and node_str == "first_q0":
                continue
            elif controller.calibration_graph == G2 and node_str in ["first_q0", "second_q0"]:
                continue
            logger_mock.assert_any_call("WORKFLOW: Diagnosing  %s.\n", node_str)

        # Assert that no node has been marked as passed:
        for node in nodes.values():
            assert node.checkpoint_passed is None

        # Asserts recursive calls
        controller.calibrate.assert_not_called()
        controller._update_parameters.assert_not_called()


#########################################
### TEST CHECKPOINT PASSED COMPARISON ###
#########################################
@pytest.mark.parametrize(
    "controller",
    [
        CalibrateAllMockedController(node_sequence=nodes, calibration_graph=graph, runcard=path_runcard)
        for graph in good_graphs
    ],
)
class TestCheckpointPassedComparison:
    """Test that the ``checkpoint_passed_comparison()`` method behaves well."""


    def test_checkpoint_passed_comparison(self, controller: CalibrateAllMockedController):
        """Test that the ``checkpoint_passed_comparison()`` method behaves well."""

        # Assert that if no check_value is set, the method returns True:
        nodes_w_cp["first_cp_q0"].check_value = None
        assert controller._checkpoint_passed_comparison(nodes_w_cp["first_cp_q0"]) is True
        nodes_w_cp["first_cp_q0"].check_value = {"fidelity_first": 0.9}

        # Assert that if no output_parameters, the method returns False:
        nodes_w_cp["first_cp_q0"].output_parameters = None
        assert controller._checkpoint_passed_comparison(nodes_w_cp["first_cp_q0"]) is False

        # Assert that if fidelity>check_value, the method returns True:
        nodes_w_cp["first_cp_q0"].output_parameters = {"fidelities": {"fidelity_first": 0.95}}
        assert controller._checkpoint_passed_comparison(nodes_w_cp["first_cp_q0"]) is True

        # Assert that if fidelity<check_value, the method returns False:
        nodes_w_cp["first_cp_q0"].output_parameters = {"fidelities": {"fidelity_first": 0.85}}
        assert controller._checkpoint_passed_comparison(nodes_w_cp["first_cp_q0"]) is False



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
    def test_calibrate(self, mock_add_str, mock_run, controller: CalibrationController):
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
    def test_update_parameters(self, mock_save_platform, mock_set_params, controller: CalibrationController):
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
    def test_get_last_set_parameters(self, controller: CalibrationController):
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
    def test_get_last_fidelities(self, controller: CalibrationController):
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
    def test_get_qubits_table_and_test_create_empty_dataframe(self, controller: CalibrationController):
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

    def test_reorder_fidelities(self, controller: CalibrationController):
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
    def test_dependencies(self, controller: CalibrationController):
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
