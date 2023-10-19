import itertools
import os
from unittest.mock import MagicMock, call

import networkx as nx
import pytest

from qililab.automatic_calibration import CalibrationController, CalibrationNode, norm_root_mean_sqrt_error
from qililab.data_management import build_platform
from qililab.platform.platform import Platform

########################
### DIRECTORY CHANGE ###
########################
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
path_runcard = abspath.split("qililab")[0] + "qililab/examples/runcards/galadriel.yml"


######################
### NODES CREATION ###
######################
zeroth = CalibrationNode(
    nb_path="notebook_test/zeroth.ipynb",
    in_spec_threshold=4,
    bad_data_threshold=8,
    comparison_model=norm_root_mean_sqrt_error,
    drift_timeout=1.0,
)
first = CalibrationNode(
    nb_path="notebook_test/first.ipynb",
    in_spec_threshold=4,
    bad_data_threshold=8,
    comparison_model=norm_root_mean_sqrt_error,
    drift_timeout=1800.0,
)
second = CalibrationNode(
    nb_path="notebook_test/second.ipynb",
    in_spec_threshold=2,
    bad_data_threshold=4,
    comparison_model=norm_root_mean_sqrt_error,
    drift_timeout=1.0,
)
third = CalibrationNode(
    nb_path="notebook_test/third.ipynb",
    in_spec_threshold=1,
    bad_data_threshold=2,
    comparison_model=norm_root_mean_sqrt_error,
    drift_timeout=1.0,
)
fourth = CalibrationNode(
    nb_path="notebook_test/fourth.ipynb",
    in_spec_threshold=1,
    bad_data_threshold=2,
    comparison_model=norm_root_mean_sqrt_error,
    drift_timeout=1.0,
)

# NODE MAPPING TO THE GRAPH (key = name in graph, value = node object):
nodes = {"zeroth": zeroth, "first": first, "second": second, "third": third, "fourth": fourth}

# GOOD GRAPH CREATION:
G0 = nx.DiGraph()  #       3 <--\
G0.add_edge("fourth", "third")  #             \
G0.add_edge("fourth", "second")  # 0 <-- 2 <-- 4
G0.add_edge("second", "zeroth")  # ^\
G0.add_edge("first", "zeroth")  #   \---1

# GOOD GRAPH CREATION:
G1 = nx.DiGraph()  #       3 <--\
G1.add_edge("fourth", "third")  #       v     \
G1.add_edge("fourth", "second")  # 0 <-- 2 <--- 4
G1.add_edge("second", "zeroth")  # ^\    v
G1.add_edge("first", "zeroth")  #   \---1
G1.add_edge("third", "second")
G1.add_edge("second", "first")

# GOOD GRAPH CREATION:
G2 = nx.DiGraph()  #   /-- 3 <-- 4
G2.add_edge("fourth", "third")  #  /
G2.add_edge("third", "zeroth")  # 0 <-- 2
G2.add_edge("second", "zeroth")  #  \
G2.add_edge("first", "zeroth")  #   \-- 1

# GOOD GRAPH CREATION:
G3 = nx.DiGraph()
G3.add_edge("fourth", "third")  #   /-- 3 <-- 4
G3.add_edge("third", "zeroth")  #  /    v
G3.add_edge("third", "second")  # 0 <-- 2
G3.add_edge("second", "zeroth")  #  \
G3.add_edge("first", "zeroth")  #   \-- 1

# GOOD GRAPH CREATION:
G4 = nx.DiGraph()
G4.add_edge("fourth", "third")  #   /-- 2 <--\
G4.add_edge("third", "second")  #  /          \
G4.add_edge("third", "first")  # 0            3 <-- 4
G4.add_edge("second", "zeroth")  #  \          /
G4.add_edge("first", "zeroth")  #   \-- 1 <--/

# GOOD GRAPH CREATION:
G5 = nx.DiGraph()
G5.add_edge("fourth", "third")  #   /-- 2 <--\
G5.add_edge("third", "second")  #  /    |     \
G5.add_edge("third", "first")  # 0     |      3 <-- 4
G5.add_edge("second", "zeroth")  #  \    v     /
G5.add_edge("second", "first")  #   \-- 1 <--/
G5.add_edge("first", "zeroth")

# GOOD GRAPH CREATION:
G6 = nx.DiGraph()
G6.add_edge("fourth", "third")  #   /-- 3 <--\
G6.add_edge("third", "second")  #  /    v     \
G6.add_edge("third", "zeroth")  # 0 <-- 2      4
G6.add_edge("second", "zeroth")  #  \    ^     /
G6.add_edge("first", "second")  #   \-- 1 <--/
G6.add_edge("first", "zeroth")
G6.add_edge("fourth", "first")

# GOOD GRAPH CREATION:
G7 = nx.DiGraph()
G7.add_edge("fourth", "third")  #   /-- 3 <--\
G7.add_edge("third", "second")  #  /    v     \
G7.add_edge("third", "zeroth")  # 0 <-- 2      4
G7.add_edge("second", "zeroth")  #  \    v     /
G7.add_edge("second", "first")  #   \-- 1 <--/
G7.add_edge("first", "zeroth")
G7.add_edge("fourth", "first")

# GOOD GRAPH CREATION:
G8 = nx.DiGraph()
G8.add_edge("fourth", "third")  #   /-- 3 <--\
G8.add_edge("third", "second")  #  /    v     \
G8.add_edge("third", "zeroth")  # 0 <-- 2 <--- 4
G8.add_edge("second", "zeroth")  #  \    ^     /
G8.add_edge("first", "second")  #   \-- 1 <--/
G8.add_edge("first", "zeroth")
G8.add_edge("fourth", "second")
G8.add_edge("fourth", "first")

# GOOD GRAPH CREATION:              #       ^
G9 = nx.DiGraph()  #       |
G9.add_edge("fourth", "third")  #   /-- 3 <--\
G9.add_edge("third", "second")  #  /    v     \
G9.add_edge("third", "zeroth")  # 0 <-- 2 <--- 4
G9.add_edge("second", "zeroth")  #  \    ^     /
G9.add_edge("first", "second")  #   \-- 1 <--/
G9.add_edge("first", "zeroth")  #       ^
G9.add_edge("fourth", "second")  #       |
G9.add_edge("fourth", "first")
G9.add_edge("third", "first")

# BAD GRAPH CREATION:
B = nx.DiGraph()  #         /--->---\
B.add_edge("fourth", "third")  #        /         \
B.add_edge("third", "second")  # 0 <-- 1 <-- 2 <-- 3 <-- 4
B.add_edge("second", "first")
B.add_edge("first", "zeroth")
B.add_edge("first", "third")

good_graphs = [G0, G1, G2, G3, G4, G5, G6, G7, G8, G9]

# Recursive calls of each graph, when you maintain node 4.
G0_calls = [call(third), call(zeroth), call(second), call(fourth)]
G1_calls = [
    call(zeroth),
    call(zeroth),
    call(first),
    call(second),
    call(third),
    call(zeroth),
    call(zeroth),
    call(first),
    call(second),
    call(fourth),
]
G2_calls = [call(zeroth), call(third), call(fourth)]
G3_calls = [call(zeroth), call(zeroth), call(second), call(third), call(fourth)]
G4_calls = [call(zeroth), call(second), call(zeroth), call(first), call(third), call(fourth)]
G5_calls = [call(zeroth), call(zeroth), call(first), call(second), call(zeroth), call(first), call(third), call(fourth)]
G6_calls = [
    call(zeroth),
    call(second),
    call(zeroth),
    call(third),
    call(zeroth),
    call(second),
    call(zeroth),
    call(first),
    call(fourth),
]
G7_calls = [
    call(zeroth),
    call(zeroth),
    call(first),
    call(second),
    call(zeroth),
    call(third),
    call(zeroth),
    call(first),
    call(fourth),
]
G8_calls = [
    call(zeroth),
    call(second),
    call(zeroth),
    call(third),
    call(zeroth),
    call(second),
    call(zeroth),
    call(second),
    call(zeroth),
    call(first),
    call(fourth),
]
G9_calls = [
    call(zeroth),
    call(second),
    call(zeroth),
    call(zeroth),
    call(second),
    call(zeroth),
    call(first),
    call(third),
    call(zeroth),
    call(second),
    call(zeroth),
    call(second),
    call(zeroth),
    call(first),
    call(fourth),
]

good_graphs_calls_for_maintain4 = [
    G0_calls,
    G1_calls,
    G2_calls,
    G3_calls,
    G4_calls,
    G5_calls,
    G6_calls,
    G7_calls,
    G8_calls,
    G9_calls,
]


##########################
### MOCKED CONTROLLERS ###
##########################
class MaintainMockedController(CalibrationController):
    """`CalibrationController` to test the workflow of `maintain()` where we mocked `check_state()`, `check_data()`, `diagnose()`, `calibrate()` and `update_parameters()`."""

    def __init__(self, node_sequence, calibration_graph, runcard, check_state: bool, check_data: str):
        super().__init__(node_sequence=node_sequence, calibration_graph=calibration_graph, runcard=runcard)
        self.check_state = MagicMock(return_value=check_state)
        self.check_data = MagicMock(return_value=check_data)
        self.diagnose = MagicMock(return_value=None)
        self.calibrate = MagicMock(return_value=None)
        self._update_parameters = MagicMock(return_value=None)


class RunAutomaticCalibrationMockedController(CalibrationController):
    """`CalibrationController` to test the workflow of `run_automatic_calibration()`, with `maintain()` mocked."""

    def __init__(self, node_sequence, calibration_graph, runcard):
        super().__init__(node_sequence=node_sequence, calibration_graph=calibration_graph, runcard=runcard)
        self.maintain = MagicMock(return_value=None)


###################
### TESTS START ###
###################
class TestCalibrationControllerInitialization:
    """Unit tests for the CalibrationController class initialization"""

    @pytest.mark.parametrize(
        "controller",
        [
            (graph, CalibrationController(node_sequence=nodes, calibration_graph=graph, runcard=path_runcard))
            for graph in good_graphs
        ],
    )
    def test_good_init_method(self, controller):
        """Test a valid initialization of the class"""

        assert controller[1].calibration_graph == controller[0]
        assert isinstance(controller[1].calibration_graph, nx.DiGraph)
        assert controller[1].node_sequence == nodes
        assert isinstance(controller[1].node_sequence, dict)
        assert controller[1].runcard == path_runcard
        assert isinstance(controller[1].runcard, str)
        assert controller[1].platform.to_dict() == build_platform(path_runcard).to_dict()
        assert isinstance(controller[1].platform, Platform)

    def test_bad_init_method(self):
        """Test an invalid initialization of the class"""
        with pytest.raises(ValueError) as error:
            _ = CalibrationController(node_sequence=nodes, calibration_graph=B, runcard=path_runcard)

        assert str(error.value) == "The calibration graph must be a Directed Acyclic Graph (DAG)."


class TestCalibrationController:
    """Test CalibrationController behaves well for any returns of the `check_sate()` and `check_data()`."""

    @pytest.mark.parametrize(
        "controller",
        [
            (
                graph,
                RunAutomaticCalibrationMockedController(
                    node_sequence=nodes, calibration_graph=graph, runcard=path_runcard
                ),
            )
            for graph in good_graphs
        ],
    )
    def test_run_automatic_calibration(self, controller):
        """Test that `run_automatic_calibration()` gets the proper nodes to maintain."""
        controller[1].run_automatic_calibration()

        if controller[0] in [G0, G3]:
            controller[1].maintain.assert_any_call(fourth)
            controller[1].maintain.assert_any_call(first)
            assert controller[1].maintain.call_count == 2

        elif controller[0] == G2:
            controller[1].maintain.assert_any_call(fourth)
            controller[1].maintain.assert_any_call(second)
            controller[1].maintain.assert_any_call(first)
            assert controller[1].maintain.call_count == 3

        elif controller[0] in [G1, G4, G5, G6, G7, G8, G9]:
            controller[1].maintain.assert_any_call(fourth)
            assert controller[1].maintain.call_count == 1

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
    def test_low_level_mockings_working_properly(self, controller):
        """Test that the mockings are working properly."""
        assert controller[3].check_state() == controller[0]
        assert controller[3].check_data() == controller[1]
        assert controller[3].diagnose() is None
        assert controller[3].calibrate() is None
        assert controller[3]._update_parameters() is None

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
    def test_maintain_recursive_maintain_and_check_status_calls(self, controller):
        """Test that maintain follows the correct logic for each graph, starting from node 4.

        The check status shouldn't change the recursive workflow, they would just create diagnoses & calibrates in the middle.
        """
        controller[3].maintain(fourth)
        # Assert workflow if we start maintain in the fourth node for each graph!
        controller[3].check_state.assert_has_calls(good_graphs_calls_for_maintain4[good_graphs.index(controller[2])])

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
    def test_maintain_recursive_check_data_diagnose_calibrate_and_update_params_calls(self, controller):
        """Test that maintain arrives to check_data or not, the correct quantity of times for each graph, starting from node 4."""
        controller[3].maintain(fourth)

        # Assert workflow if we start maintain in the fourth node for each graph!
        if controller[3].check_state() is True:
            controller[3].check_data.assert_not_called()
            controller[3].diagnose.assert_not_called()
            controller[3].calibrate.assert_not_called()
            controller[3]._update_parameters.assert_not_called()

        elif controller[3].check_data() == "in_spec":
            controller[3].diagnose.assert_not_called()
            controller[3].calibrate.assert_not_called()
            controller[3]._update_parameters.assert_not_called()
            controller[3].check_data.assert_has_calls(good_graphs_calls_for_maintain4[good_graphs.index(controller[2])])

        elif controller[3].check_data() == "out_of_spec":
            controller[3].diagnose.assert_not_called()
            controller[3].check_data.assert_has_calls(good_graphs_calls_for_maintain4[good_graphs.index(controller[2])])
            controller[3].calibrate.assert_has_calls(good_graphs_calls_for_maintain4[good_graphs.index(controller[2])])
            controller[3]._update_parameters.assert_has_calls(
                good_graphs_calls_for_maintain4[good_graphs.index(controller[2])]
            )

        elif controller[3].check_data() == "bad_data":
            controller[3].check_data.assert_has_calls(good_graphs_calls_for_maintain4[good_graphs.index(controller[2])])
            controller[3].calibrate.assert_has_calls(good_graphs_calls_for_maintain4[good_graphs.index(controller[2])])
            controller[3]._update_parameters.assert_has_calls(
                good_graphs_calls_for_maintain4[good_graphs.index(controller[2])]
            )

            # Check diagnose for each dependant:
            dependants_calls = []
            for node_call in good_graphs_calls_for_maintain4[good_graphs.index(controller[2])]:
                for node_name in controller[2].successors(node_call.args[0].node_id):
                    dependants_calls.append(call(controller[3].node_sequence[node_name]))
            controller[3].diagnose.assert_has_calls(dependants_calls)


#     # Test _is_timeout_expired
#     @pytest.mark.parametrize(
#         "timestamp, timeout, expected",
#         [
#             (10, 20, True),
#             (100, 50, False)
#         ],
#         ids=["expired", "not expired"]
#     )
#     def test_is_timeout_expired(timestamp, timeout, expected):

#         # Arrange
#         with patch("qililab.automatic_calibration.calibration_controller.datetime") as mock_datetime:
#             mock_datetime.now.return_value = datetime(2022, 1, 1, 0, 0, 0)
#             mock_datetime.fromtimestamp.return_value = datetime(1970, 1, 1, 0, 0, timestamp)

#             # Act
#             result = CalibrationController._is_timeout_expired(timestamp, timeout)

#         # Assert
#         assert result == expected

#         def test_diagnose():
#         # Arrange
#         node = CalibrationNode("node1")
#         controller = CalibrationController(nx.DiGraph(), {"node1": node}, "runcard.yml")
#         controller.check_data = MagicMock(return_value="bad_data")
#         controller.calibrate = MagicMock()
#         controller._update_parameters = MagicMock()

#         # Act
#         result = controller.diagnose(node)

#         # Assert
#         assert result == True
#         controller.check_data.assert_called_once_with(node)
#         controller.calibrate.assert_called_once_with(node)
#         controller._update_parameters.assert_called_once_with(node=node)

#     def test_diagnose_in_spec():
#         # Arrange
#         node = CalibrationNode("node1")
#         controller = CalibrationController(nx.DiGraph(), {"node1": node}, "runcard.yml")
#         controller.check_data = MagicMock(return_value="in_spec")

#         # Act
#         result = controller.diagnose(node)

#         # Assert
#         assert result == False
#         controller.check_data.assert_called_once_with(node)
#         assert not controller.calibrate.called
#         assert not controller._update_parameters.called


#     # Tests for check_state()
#     def test_check_state_true():
#         # Arrange
#         node = CalibrationNode("node1")
#         node.previous_timestamp = 10
#         node.drift_timeout = 20
#         controller = CalibrationController(nx.DiGraph(), {"node1": node}, "runcard.yml")

#         # Act
#         result = controller.check_state(node)

#         # Assert
#         assert result == True

#     def test_check_state_false():
#         # Arrange
#         node = CalibrationNode("node1")
#         node.previous_timestamp = None
#         controller = CalibrationController(nx.DiGraph(), {"node1": node}, "runcard.yml")

#         # Act
#         result = controller.check_state(node)

#         # Assert
#         assert result == False


#     # Tests for check_data()
#     # Mock implementation

#     # Tests for calibrate()
#     # Mock implementation

#     # Tests for _update_parameters()
#     # Mock implementation

#     # Tests for _dependents()
#     def test_dependents():
#         # Arrange
#         graph = nx.DiGraph()
#         graph.add_edges_from([("A", "B"), ("B", "C")])
#         nodes = {"A": "nodeA", "B": "nodeB", "C": "nodeC"}
#         controller = CalibrationController(graph, nodes, "runcard.yml")

#         # Act
#         result = controller._dependents(nodes["B"])

#         # Assert
#         assert result == [nodes["C"]]

#     # Tests for _is_timeout_expired()
#     # (already shown in previous example)
