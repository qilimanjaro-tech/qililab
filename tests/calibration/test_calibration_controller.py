import itertools
from datetime import datetime
from unittest.mock import MagicMock, call, patch

import networkx as nx
import pandas as pd
import pytest

from qililab.calibration import CalibrationController, CalibrationNode
from qililab.data_management import build_platform
from qililab.platform.platform import Platform

# flake8: noqa
# pylint: disable=protected-access

#################################################################################
#################################### SET UPS ####################################
#################################################################################

path_runcard = "examples/runcards/galadriel.yml"


def dummy_comparison_model(obtained: dict, comparison: dict) -> float:
    """Basic comparison model for testing."""
    return abs(sum(obtained["y"]) - sum(comparison["y"]))


######################
### NODES CREATION ###
######################
zeroth = CalibrationNode(
    nb_path="tests/calibration/notebook_test/zeroth.ipynb",
    qubit_index=[0, 1],  # qubit_index as list
    in_spec_threshold=4,  # in_spec thresholds
    bad_data_threshold=8,
    comparison_model=dummy_comparison_model,
    drift_timeout=1.0,
)
first = CalibrationNode(
    nb_path="tests/calibration/notebook_test/first.ipynb",
    qubit_index=0,
    in_spec_threshold=4,  # in_spec thresholds
    bad_data_threshold=8,
    comparison_model=dummy_comparison_model,
    drift_timeout=1.0,  # long drift timeout
)
second = CalibrationNode(
    nb_path="tests/calibration/notebook_test/second.ipynb",
    qubit_index=0,
    in_spec_threshold=2,  # out_of_spec thresholds
    bad_data_threshold=4,
    comparison_model=dummy_comparison_model,
    drift_timeout=1.0,
)
third = CalibrationNode(
    nb_path="tests/calibration/notebook_test/third.ipynb",
    qubit_index=0,
    in_spec_threshold=1,  # bad_data thresholds
    bad_data_threshold=2,
    comparison_model=dummy_comparison_model,
    drift_timeout=1.0,
)
fourth = CalibrationNode(
    nb_path="tests/calibration/notebook_test/fourth.ipynb",
    # no qubit index
    in_spec_threshold=1,  # bad_data thresholds
    bad_data_threshold=2,
    comparison_model=dummy_comparison_model,
    drift_timeout=1.0,
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

# Leaves to Roots recursive calls of each graph. Examples: Maintain(fourth), or calibrate and update_param in Diagnose(fourth).
G0_calls = [call(third), call(zeroth), call(second), call(fourth)]
G1_calls = [call(zeroth),call(zeroth),call(first),call(second),call(third),call(zeroth),call(zeroth),call(first),call(second),call(fourth)]
G2_calls = [call(zeroth), call(third), call(fourth)]
G3_calls = [call(zeroth), call(zeroth), call(second), call(third), call(fourth)]
G4_calls = [call(zeroth), call(second), call(zeroth), call(first), call(third), call(fourth)]
G5_calls = [call(zeroth), call(zeroth), call(first), call(second), call(zeroth), call(first), call(third), call(fourth)]
G6_calls = [call(zeroth),call(second),call(zeroth),call(third),call(zeroth),call(second),call(zeroth),call(first),call(fourth)]
G7_calls = [call(zeroth),call(zeroth),call(first),call(second),call(zeroth),call(third),call(zeroth),call(first),call(fourth)]
G8_calls = [call(zeroth),call(second),call(zeroth),call(third),call(zeroth),call(second),call(zeroth),call(second),call(zeroth),call(first),call(fourth)]
G9_calls = [call(zeroth),call(second),call(zeroth),call(zeroth),call(second),call(zeroth),call(first),call(third),call(zeroth),call(second),call(zeroth),call(second),call(zeroth),call(first),call(fourth)]

leaves_to_roots_good_graphs_calls = [G0_calls,G1_calls,G2_calls,G3_calls,G4_calls,G5_calls,G6_calls,G7_calls,G8_calls,G9_calls]

# Roots to Leaves recursive calls of each graph. Examples: Diagnose(fourth) recursive check_data calls.
G0_calls = [call(fourth), call(third), call(second), call(zeroth)]
G1_calls = [call(fourth), call(third), call(second), call(zeroth), call(first), call(zeroth), call(second), call(zeroth)]
G2_calls = [call(fourth), call(third), call(zeroth)]
G3_calls = [call(fourth), call(third), call(zeroth), call(second), call(zeroth)]
G4_calls = [call(fourth), call(third), call(second), call(zeroth), call(first), call(zeroth)]
G5_calls = [call(fourth), call(third), call(second), call(zeroth), call(first), call(zeroth), call(first), call(zeroth)]
G6_calls = [call(fourth),call(third),call(second),call(zeroth),call(zeroth),call(first),call(second),call(zeroth),call(zeroth)]
G7_calls = [call(fourth),call(third),call(second),call(zeroth),call(first),call(zeroth),call(zeroth),call(first),call(zeroth)]
G8_calls = [call(fourth),call(third),call(second),call(zeroth),call(zeroth),call(second),call(zeroth),call(first),call(second),call(zeroth),call(zeroth)]
G9_calls = [call(fourth),call(third),call(second),call(zeroth),call(zeroth),call(first),call(second),call(zeroth),call(zeroth),call(second),call(zeroth),call(first),call(second),call(zeroth),call(zeroth)]

roots_to_leaves_good_graphs_calls = [G0_calls,G1_calls,G2_calls,G3_calls,G4_calls,G5_calls,G6_calls,G7_calls,G8_calls,G9_calls]

# fmt: on


##########################
### MOCKED CONTROLLERS ###
##########################
class RunAutomaticCalibrationMockedController(CalibrationController):
    """``CalibrationController`` to test the workflow of ``run_automatic_calibration()``, where its mocked ``maintain()``, ``get_last_set_parameters()`` and ``get_last_fidelities()``."""

    def __init__(self, node_sequence, calibration_graph, runcard):
        super().__init__(node_sequence=node_sequence, calibration_graph=calibration_graph, runcard=runcard)
        self.maintain = MagicMock(return_value=None)
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


# type: ignore[method-assign]
class MaintainMockedController(CalibrationController):
    """``CalibrationController`` to test the workflow of ``maintain()`` where its mocked ``check_state()``, ``check_data()``, ``diagnose()``, ``calibrate()`` and ``update_parameters()``."""

    def __init__(self, node_sequence, calibration_graph, runcard, check_state: bool, check_data: str):
        super().__init__(node_sequence=node_sequence, calibration_graph=calibration_graph, runcard=runcard)
        self.check_state = MagicMock(return_value=check_state)
        self.check_data = MagicMock(return_value=check_data)
        self.diagnose = MagicMock(return_value=None)
        self.calibrate = MagicMock(return_value=None)
        self._update_parameters = MagicMock(return_value=None)


# type: ignore[method-assign]
class DiagnoseMockedController(CalibrationController):
    """`CalibrationController` to test the workflow of `diagnose()` where its mocked ``check_data()``, ``calibrate()`` and ``update_parameters()``."""

    def __init__(self, node_sequence, calibration_graph, runcard, check_data: str):
        super().__init__(node_sequence=node_sequence, calibration_graph=calibration_graph, runcard=runcard)
        self.check_data = MagicMock(return_value=check_data)
        self.calibrate = MagicMock(return_value=None)
        self._update_parameters = MagicMock(return_value=None)


# type: ignore[method-assign]
class DiagnoseFixedMockedController(CalibrationController):
    """`CalibrationController` to test the workflow of `diagnose()` where its mocked ``check_data()``, ``calibrate()`` and ``update_parameters()``."""

    def __init__(self, node_sequence, calibration_graph, runcard, check_data):
        super().__init__(node_sequence=node_sequence, calibration_graph=calibration_graph, runcard=runcard)
        self.calibrate = MagicMock(return_value=None)
        self._update_parameters = MagicMock(return_value=None)
        self.check_data_string = check_data

    def check_data(self, node):
        return self.check_data_string if node == zeroth else "bad_data"


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

    # TODO: Add functionality for new flags, and new changes!
    # def test_run_automatic_calibration(self, controller):
    #     """Test that `run_automatic_calibration()` gets the proper nodes to maintain."""
    #     # Act:
    #     output_dict = controller.run_automatic_calibration()

    #     # Asserts:
    #     controller.get_last_set_parameters.assert_called_once_with()
    #     controller.get_last_fidelities.assert_called_once_with()
    #     assert output_dict == {
    #         "set_parameters": {("test", "test"): (0.0, "test", datetime.fromtimestamp(1999))},
    #         "fidelities": {"test": (0.0, "test", datetime.fromtimestamp(1999))},
    #     }

    #     # sourcery skip: extract-duplicate-method
    #     if controller.calibration_graph in [G0, G3]:
    #         controller.maintain.assert_any_call(fourth)
    #         controller.maintain.assert_any_call(first)
    #         assert controller.maintain.call_count == 2
    #         # assert mock_force_condition.call_count == 2

    #     elif controller.calibration_graph == G2:
    #         controller.maintain.assert_any_call(fourth)
    #         controller.maintain.assert_any_call(second)
    #         controller.maintain.assert_any_call(first)
    #         assert controller.maintain.call_count == 3
    #         # assert mock_force_condition.call_count == 3

    #     elif controller.calibration_graph in [G1, G4, G5, G6, G7, G8, G9]:
    #         controller.maintain.assert_any_call(fourth)
    #         assert controller.maintain.call_count == 1
    #         # assert mock_force_condition.call_count == 1


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

        # Act:
        controller[2].calibrate_all(fourth)

        # Asserts recursive calls
        controller[2].calibrate.assert_has_calls(controller[1])
        controller[2]._update_parameters.assert_has_calls(controller[1])


#####################
### TEST MAINTAIN ###
#####################
@pytest.mark.parametrize(
    "controller",
    [
        (
            i,
            j,
            graph,
            MaintainMockedController(
                node_sequence=nodes, calibration_graph=graph, runcard=path_runcard, check_state=i, check_data=j
            ),
        )
        for i, j, graph in itertools.product([True, False], ["bad_data", "in_spec", "out_of_spec"], good_graphs)
    ],
)
class TestMaintainFromCalibrationController:
    """Test that ``maintain()`` of ``CalibrationController`` behaves well."""

    def test_low_level_mockings_working_properly(self, controller):
        """Test that the mockings are working properly."""
        # Assert:
        assert controller[3].check_state() == controller[0]
        assert controller[3].check_data() == controller[1]
        assert controller[3].diagnose() is None
        assert controller[3].calibrate() is None
        assert controller[3]._update_parameters() is None

    # TODO: Change test for new workflow!
    # def test_maintain_same_node_functions_calls_from_leave(self, controller):
    #     """Test that ``maintain`` follows the correct logic for each graph, starting from node zeroth "leave".

    #     This "leave" case should not have recursive calls.
    #     """
    #     # Reset mock calls:
    #     controller[3].check_state.reset_mock()
    #     controller[3].check_data.reset_mock()
    #     controller[3].diagnose.reset_mock()
    #     controller[3].calibrate.reset_mock()
    #     controller[3]._update_parameters.reset_mock()

    #     # Act:
    #     controller[3].maintain(zeroth)

    #     # Assert workflow if we start maintain in the zeroth node for each graph!
    #     controller[3].check_state.assert_called_once_with(zeroth)
    #     controller[3].diagnose.assert_not_called()

    #     # if check_status is True
    #     if controller[0]:
    #         controller[3].check_data.assert_not_called()
    #         controller[3].calibrate.assert_not_called()
    #         controller[3]._update_parameters.assert_not_called()

    #     # elif check_data is in_spec
    #     elif controller[1] == "in_spec":
    #         controller[3].check_data.assert_called_once_with(zeroth)
    #         controller[3].calibrate.assert_not_called()
    #         controller[3]._update_parameters.assert_not_called()

    #     # elif check_data is out_of_spec or bad_data
    #     elif controller[1] in ["out_of_spec", "bad_data"]:
    #         controller[3].check_data.assert_called_once_with(zeroth)
    #         controller[3].calibrate.assert_called_once_with(zeroth)
    #         controller[3]._update_parameters.assert_called_once_with(zeroth)

    # TODO: Change test for new workflow!
    # def test_maintain_recursive_maintain_and_check_status_calls_from_root(self, controller):
    #     """Test that ``maintain`` recursive calls work correctly for each graph, starting from node fourth "root".

    #     The check status shouldn't change the recursive workflow, they would just create diagnoses & calibrates in the middle.
    #     """
    #     # Reset mock calls:
    #     controller[3].check_state.reset_mock()

    #     # Act:
    #     controller[3].maintain(fourth)

    #     # Assert workflow if we start maintain in the fourth node for each graph!
    #     controller[3].check_state.assert_has_calls(leaves_to_roots_good_graphs_calls[good_graphs.index(controller[2])])

    # TODO: Change test for new workflow!
    # def test_maintain_recursive_functions_calls_from_root(self, controller):
    #     """Test that ``maintain`` follows the correct logic for each graph, starting from node fourth "root".

    #     This "root" case should have recursive calls.
    #     """
    #     # Reset mock calls:
    #     controller[3].check_state.reset_mock()
    #     controller[3].check_data.reset_mock()
    #     controller[3].diagnose.reset_mock()
    #     controller[3].calibrate.reset_mock()
    #     controller[3]._update_parameters.reset_mock()

    #     # Act:
    #     controller[3].maintain(fourth)

    #     # Assert workflow if we start maintain in the fourth node for each graph!
    #     controller[3].check_state.assert_has_calls(leaves_to_roots_good_graphs_calls[good_graphs.index(controller[2])])

    #     # if check_state is False
    #     if controller[0] is True:
    #         controller[3].check_data.assert_not_called()
    #         controller[3].diagnose.assert_not_called()
    #         controller[3].calibrate.assert_not_called()
    #         controller[3]._update_parameters.assert_not_called()

    #     # elif check_data is in_spec
    #     elif controller[1] == "in_spec":
    #         controller[3].diagnose.assert_not_called()
    #         controller[3].calibrate.assert_not_called()
    #         controller[3]._update_parameters.assert_not_called()
    #         controller[3].check_data.assert_has_calls(
    #             leaves_to_roots_good_graphs_calls[good_graphs.index(controller[2])]
    #         )

    #     # elif check_data is out_of_spec
    #     elif controller[1] == "out_of_spec":
    #         controller[3].diagnose.assert_not_called()
    #         controller[3].check_data.assert_has_calls(
    #             leaves_to_roots_good_graphs_calls[good_graphs.index(controller[2])]
    #         )
    #         controller[3].calibrate.assert_has_calls(
    #             leaves_to_roots_good_graphs_calls[good_graphs.index(controller[2])]
    #         )
    #         controller[3]._update_parameters.assert_has_calls(
    #             leaves_to_roots_good_graphs_calls[good_graphs.index(controller[2])]
    #         )

    #     # elif check_data is bad_data
    #     elif controller[1] == "bad_data":
    #         controller[3].check_data.assert_has_calls(
    #             leaves_to_roots_good_graphs_calls[good_graphs.index(controller[2])]
    #         )
    #         controller[3].calibrate.assert_has_calls(
    #             leaves_to_roots_good_graphs_calls[good_graphs.index(controller[2])]
    #         )
    #         controller[3]._update_parameters.assert_has_calls(
    #             leaves_to_roots_good_graphs_calls[good_graphs.index(controller[2])]
    #         )

    #         # Check diagnose for each dependant:
    #         dependants_calls = []
    #         for node_call in leaves_to_roots_good_graphs_calls[good_graphs.index(controller[2])]:
    #             for node_name in controller[2].predecessors(
    #                 node_call.args[0].node_id
    #             ):  # sourcery skip: for-append-to-extend
    #                 dependants_calls.append(call(controller[3].node_sequence[node_name]))
    #         controller[3].diagnose.assert_has_calls(dependants_calls)


#####################
### TEST DIAGNOSE ###
#####################
@pytest.mark.parametrize(
    "controller",
    [
        (
            i,
            graph,
            DiagnoseMockedController(node_sequence=nodes, calibration_graph=graph, runcard=path_runcard, check_data=i),
        )
        for i, graph in itertools.product(["bad_data", "in_spec", "out_of_spec"], good_graphs)
    ],
)
class TestDiagnoseFromCalibrationController:
    """Test that the ``Diagnose`` method of ``CalibrationController`` behave well."""

    def test_low_level_mockings_working_properly(self, controller):
        """Test that the mockings are working properly."""
        # Assert:
        assert controller[2].check_data() == controller[0]
        assert controller[2].calibrate() is None
        assert controller[2]._update_parameters() is None

    def test_diagnose_functions_calls_from_leaves(self, controller):
        """Test that ``diagnose`` follows the correct logic for each graph, starting from node zeroth "leave".

        This "leave" case should not have recursive calls.
        """
        # Reset mock calls:
        controller[2].check_data.reset_mock()
        controller[2].calibrate.reset_mock()
        controller[2]._update_parameters.reset_mock()

        # Act:
        result = controller[2].diagnose(zeroth)

        # Assert workflow:
        controller[2].check_data.assert_called_once_with(zeroth)

        # elif check_data is in_spec
        if controller[0] == "in_spec":
            assert result is False
            controller[2].calibrate.assert_not_called()
            controller[2]._update_parameters.assert_called_once_with(zeroth)

        # TODO: Add functionality for safe flag, and new changes!
        # elif check_data is out_of_spec or bad_data
        # elif controller[0] in ["out_of_spec", "bad_data"]:
        #     assert result is True
        #     controller[2].calibrate.assert_called_once_with(zeroth)
        #     controller[2]._update_parameters.assert_called_once_with(zeroth)

    def test_diagnose_recursive_diagnose_and_check_data_calls_from_root(self, controller):
        """Test that ``diagnose`` recursive calls work correctly for each graph, starting from node 4.

        The result ``from check_data`` should change the recursivity.
        """
        # Reset mock calls
        controller[2].check_data.reset_mock()

        # Act
        controller[2].diagnose(fourth)

        # Assert workflow if we start diagnose in the fourth node for each graph!
        if controller[0] in ["in_spec", "out_of_spec"]:
            controller[2].check_data.assert_called_once_with(fourth)

        if controller[0] == "bad_data":
            controller[2].check_data.assert_has_calls(
                roots_to_leaves_good_graphs_calls[good_graphs.index(controller[1])]
            )

    def test_diagnose_recursive_functions_calls_from_root(self, controller):
        """Test that ``diagnose`` follows the correct logic for each graph, starting from node fourth "root".

        This "root" case should have recursive calls.
        """
        # Reset mock calls
        controller[2].check_data.reset_mock()
        controller[2].calibrate.reset_mock()
        controller[2]._update_parameters.reset_mock()

        # Act
        result = controller[2].diagnose(fourth)

        # Assert workflow:

        # elif check_data is in_spec
        if controller[0] == "in_spec":
            assert result is False
            controller[2].check_data.assert_called_once_with(fourth)
            controller[2].calibrate.assert_not_called()
            controller[2]._update_parameters.assert_called_once_with(fourth)

        # TODO: Add functionality for safe flag, and new changes!
        # elif check_data is out_of_spec or bad_data
        # elif controller[0] == "out_of_spec":
        #     assert result is True
        #     controller[2].check_data.assert_called_once_with(fourth)
        #     controller[2].calibrate.assert_called_once_with(fourth)
        #     controller[2]._update_parameters.assert_called_once_with(fourth)

        # elif controller[0] == "bad_data":
        #     assert result is True
        #     controller[2].check_data.assert_has_calls(
        #         roots_to_leaves_good_graphs_calls[good_graphs.index(controller[1])]
        #     )
        #     controller[2].calibrate.assert_has_calls(
        #         leaves_to_roots_good_graphs_calls[good_graphs.index(controller[1])]
        #     )
        #     controller[2]._update_parameters.assert_has_calls(
        #         leaves_to_roots_good_graphs_calls[good_graphs.index(controller[1])]
        #     )

    # TODO: Add functionality for safe flag, and new changes!
    # def test_diagnose_recursive_recalibrate_doesnt_find_true_from_root(self, controller):
    #     """Test that ``diagnose`` returns True correctly for when all is bad data, except a leave tested for the three options."""
    #     # sourcery skip: extract-duplicate-method
    #     # Leave in out_of_spec
    #     controller = DiagnoseFixedMockedController(
    #         node_sequence=nodes, calibration_graph=G0, runcard=path_runcard, check_data="out_of_spec"
    #     )
    #     assert controller.diagnose(zeroth) is True  # Gets calibrated
    #     assert controller.diagnose(second) is True  # Gets calibrated
    #     assert controller.diagnose(fourth) is True  # Gets calibrated

    #     # Leave in bad_data
    #     controller = DiagnoseFixedMockedController(
    #         node_sequence=nodes, calibration_graph=G0, runcard=path_runcard, check_data="bad_data"
    #     )
    #     assert controller.diagnose(zeroth) is True  # Gets calibrated
    #     assert controller.diagnose(second) is True  # Gets calibrated
    #     assert controller.diagnose(fourth) is True  # Gets calibrated

    #     # TODO: Solve that second gets calibrated for cases like this in @Isaac solving worklflow errors PR.
    #     # Leave in in_spec
    #     controller = DiagnoseFixedMockedController(
    #         node_sequence=nodes, calibration_graph=G0, runcard=path_runcard, check_data="in_spec"
    #     )
    #     assert controller.diagnose(zeroth) is False  # No calibrate
    #     assert controller.diagnose(second) is False  # No calibrate <<< WARNING, this should be calibrated!
    #     assert controller.diagnose(fourth) is True  # Calibrate (because of third)

    # TODO: DO same case with everyhting at in_spec and out_spec except zeroth


@pytest.mark.parametrize(
    "controller",
    [
        CalibrationController(node_sequence=nodes, calibration_graph=graph, runcard=path_runcard)
        for graph in good_graphs
    ],
)
class TestCalibrationController:
    """Test that the rest of ``CalibrationController`` methods behave well."""

    ########################
    ### TEST CHECK STATE ###
    ########################
    def test_check_state_for_nodes_with_no_dependencies(self, controller):
        """Test that check_state work correctly for the nodes without dependencies."""
        zeroth.previous_timestamp = datetime.now().timestamp() - 10
        zeroth.drift_timeout = 20
        result = controller.check_state(zeroth)
        assert result is True

        zeroth.previous_timestamp = datetime.now().timestamp() - 20
        zeroth.drift_timeout = 10
        result = controller.check_state(zeroth)
        assert result is False

    def test_check_state_for_nodes_with_dependencies(self, controller):
        """Test that check_state work correctly for the nodes with dependencies."""
        # Case where dependent nodes have an older timestamps, and all are passing -> True:
        for node in controller.node_sequence.values():
            node.previous_timestamp = datetime.now().timestamp() - 1000
            node.drift_timeout = 1800

        # sourcery skip: extract-duplicate-method
        fourth.previous_timestamp = datetime.now().timestamp() - 500
        result = controller.check_state(fourth)
        assert result is True

        # Case where dependent nodes have an newer timestamps, and all are passing -> False:
        fourth.previous_timestamp = datetime.now().timestamp() - 1500
        result = controller.check_state(fourth)
        assert result is False

        # Case where dependent nodes have an older timestamps, but fourth not passing -> False:
        fourth.previous_timestamp = datetime.now().timestamp() - 5
        fourth.drift_timeout = 2
        result = controller.check_state(fourth)
        assert result is False

    #######################
    ### TEST CHECK DATA ###
    #######################

    # TODO: Check why this test fails, it might be that we are skipping check_data when no previous calibration!
    # @patch("qililab.calibration.calibration_node.CalibrationNode.run_node", return_value=11.11)
    # @patch("qililab.calibration.calibration_node.CalibrationNode._add_string_to_checked_nb_name")
    # def test_check_data(self, mock_add_str, mock_run, controller):
    #     """Test that the check_data method, works correctly."""
    #     for node in controller.node_sequence.values():
    #         node.previous_output_parameters = {"check_parameters": {"x": [1, 2, 3], "y": [5, 6, 7]}}
    #         node.output_parameters = {"check_parameters": {"x": [1, 2, 3], "y": [4, 5, 6]}}
    #         node.comparison_model = dummy_comparison_model
    #         result = controller.check_data(node)

    #         if node in [zeroth, first]:
    #             assert result == "in_spec"
    #             mock_add_str.assert_called_with("in_spec", 11.11)
    #         elif node == second:
    #             assert result == "out_of_spec"
    #             mock_add_str.assert_called_with("out_of_spec", 11.11)
    #         elif node in [third, fourth]:
    #             assert result == "bad_data"
    #             mock_add_str.assert_called_with("bad_data", 11.11)

    #         mock_run.assert_called_with(check=True)

    #     assert mock_run.call_count == len(controller.node_sequence)
    #     assert mock_add_str.call_count == len(controller.node_sequence)

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

    # TODO: Check why this test doesn't work, "params" not a valid Parameter:
    # @patch("qililab.calibration.calibration_controller.Platform.set_parameter")
    # @patch("qililab.calibration.calibration_controller.save_platform")
    # def test_update_parameters(self, mock_save_platform, mock_set_params, controller):
    #     """Test that the update parameters method, calls ``platform.set_parameter()`` and ``save_platform()``."""
    #     for node in controller.node_sequence.values():
    #         node.output_parameters = {
    #             "platform_parameters": [
    #                 ("test_bus", node.qubit_index, "param", 0),
    #                 ("test_bus2", node.qubit_index, "param2", 1),
    #             ]
    #         }
    #         controller._update_parameters(node)

    #         mock_set_params.assert_called_with(
    #             alias="test_bus2", parameter="param2", value=1, channel_id=node.qubit_index
    #         )  # Checking the last call of the 2 there are.
    #         mock_save_platform.assert_called_with(controller.runcard, controller.platform)  # Checking the save call

    #     assert mock_set_params.call_count == 2 * len(controller.node_sequence)
    #     assert mock_save_platform.call_count == len(controller.node_sequence)

    ####################################
    ### TEST GET LAST SET PARAMETERS ###
    ####################################
    def test_get_last_set_parameters(self, controller):
        """Test that the ``get_last_set_parameters()`` method, gets the correct parameters."""
        for i, node in controller.node_sequence.items():
            node.output_parameters = {
                "check_parameters": {"x": [0, 1, 2, 3, 4, 5], "y": [0, 1, 2, 3, 4, 5]},
                "platform_parameters": [(f"test_bus_{i}", 0, "param", 0), (f"test_bus_{i}", 1, "param", 1)],
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
                "check_parameters": {"x": [0, 1, 2, 3, 4, 5], "y": [0, 1, 2, 3, 4, 5]},
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
                    "check_parameters": {"x": [0, 1, 2, 3, 4, 5], "y": [0, 1, 2, 3, 4, 5]},
                    "platform_parameters": [("test_bus", "0-1", f"param_{ind}", 1)],
                    "fidelities": [("0-1", f"fidelity_{ind}", 0.967)],
                }

            elif node.node_id == "fourth":
                node.node_id = "fourth_q1"
                node.output_parameters = {
                    "check_parameters": {"x": [0, 1, 2, 3, 4, 5], "y": [0, 1, 2, 3, 4, 5]},
                    "platform_parameters": [("test_bus", 1, f"param_{ind}", 1)],
                    "fidelities": [(1, f"fidelity_{ind}", 0.967)],
                }

            else:
                node.output_parameters = {
                    "check_parameters": {"x": [0, 1, 2, 3, 4, 5], "y": [0, 1, 2, 3, 4, 5]},
                    "platform_parameters": [("test_bus", 0, f"param_{ind}", 1)],
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

    #######################
    ### TEST DEPENDENTS ###
    #######################
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


class TestStaticMethodsFromCalibrationController:
    """Test that the static methods of ``CalibrationController`` behave well."""

    ##############################
    ### TEST OBTAIN COMPARISON ###
    ##############################
    def test_obtain_comparison(self):
        """Test that obtain_comparison calls comparison_model correctly."""
        controller = CalibrationController(node_sequence=nodes, calibration_graph=G1, runcard=path_runcard)

        obtained = {"x": [1, 2, 3], "y": [4, 5, 6]}
        comparison = {"x": [2, 3, 4], "y": [5, 6, 7]}

        for node in controller.node_sequence.values():
            node.comparison_model = dummy_comparison_model
            result = controller._obtain_comparison(node, obtained, comparison)

            assert result == abs(4 + 5 + 6 - 5 - 6 - 7)

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

    ######################################
    #### TEST FORCE MAINTAIN CONDITION ###
    ######################################
    # @pytest.mark.parametrize(
    #     "ratio, drift_timeout, delta_previous_timestamp, expected",
    #     [(0, 200, 800, True), (0, 5000, 400, False), (0.5, 1000, 800, True), (0.2, 1000, 100, False)],
    # )
    # def test_get_forced_maintain_condition(self, ratio, drift_timeout, delta_previous_timestamp, expected):
    #     """Test conditions are computed properly"""
    #     node = CalibrationNode(
    #         nb_path="tests/automatic_calibration/notebook_test/fourth.ipynb",
    #         in_spec_threshold=1,
    #         bad_data_threshold=2,
    #         comparison_model=dummy_comparison_model,
    #         drift_timeout=drift_timeout,
    #     )

    #     now = datetime.timestamp(datetime.now())
    #     node.previous_timestamp = now - delta_previous_timestamp

    #     assert CalibrationController._get_forced_maintain_condition(node, ratio) == expected
