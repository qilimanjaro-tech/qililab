"""Automatic-calibration Controller module, which works with notebooks as nodes."""
from typing import Callable 
import networkx as nx

from qililab.automatic_calibration.calibration_utils import is_timeout_expired
from qililab.automatic_calibration.notebook_calibration.node_minimalist import MinCalibrationNode
from qililab.data_management import build_platform, save_platform
from qililab.platform.platform import Platform

from .comparison_models import normalized_root_mean_square_error


class MinCalibrationController:
    """Class that controls the automatic calibration sequence.

    Args:
        calibration_graph (nx.DiGraph): The calibration graph. This is a directed acyclic graph where each node is a string.
        node_sequence (dict): Mapping for the dodes of the graph, from strings into the actual initialized nodes.
        runcard (str): The runcard path, containing the serialized platform where the experiments will be run.
    """

    def __init__(self, calibration_graph: nx.DiGraph, node_sequence: dict, runcard: str):
        if not nx.is_directed_acyclic_graph(calibration_graph):
            raise ValueError("The calibration graph must be a Directed Acyclic Graph (DAG).")
        
        self.calibration_graph: nx.DiGraph = calibration_graph
        """The calibration graph. This is a directed acyclic graph where each node is a string."""
        
        self.node_sequence: dict = node_sequence
        """Mapping for the dodes of the graph, from strings into the actual initialized nodes."""
        
        self.runcard: str = runcard
        """The runcard path, containing the serialized platform where the experiments will be run."""
        
        self.platform: Platform = build_platform(runcard)
        """The initialized platform, where the experiments will be run."""

    def maintain(self, node: MinCalibrationNode) -> None:
        """This is primary interface for our calibration procedure and it's the highest level algorithm.
        We call maintain on the node that we want in spec, and maintain will call all the subroutines necessary to do that.
        We design 'maintain' to start actually acquiring data (by calling 'check_data' or 'calibrate') in the optimal location
        in the graph to avoid extra work: for example if node A depends on node B, before trying to calibrate node A we check
        the state of node B. If node B is out of spec or has bad data, calibrating A will be a waste of resource because we
        will be doing so based on faulty data.

        Args:
            node (CalibrationNode): The node where we want to start the algorithm. At the beginning of the calibration procedure,
                                this node will be the highest level node in the calibration graph.
        """
        print(f"maintaining {node.node_id}!!!\n")
        # Recursion over all the nodes that the current node depends on.
        for n in self.dependents(node):
            print(f"maintaining {n.node_id} from maintain({node.node_id})!!!\n")
            self.maintain(n)

        if self.check_state(node):
            return

        result = self.check_data(node)
        if result == "in_spec":
            return
        elif result == "bad_data":
            for n in self.dependents(node):
                self.diagnose(n)

        # calibrate
        self.calibrate(node)

        # GALADRIEL: uncomment when platform is connected
        self.update_parameters(node=node)

    def diagnose(self, node: MinCalibrationNode) -> bool:
        """This is a method called by `maintain` in the special case that its call of `check_data` finds bad data.
        `maintain` assumes that our knowledge of the state of the system matches the actual state of the
        system: if we knew a node would return bad data, we wouldn't bother running experiments on it.
        The fact that check_data returns bad data means that that's not the case: out knowledge of the state
        of the system is inaccurate. The purpose of diagnose is to repair inaccuracies in our knowledge of the
        state of the system so that maintain can resume.

        Args:
            node (CalibrationNode): The node where we want to start the algorithm.

        Returns:
            bool: True is there have been recalibrations, False otherwise. The return value is only used by recursive calls.
        """
        print(f"diagnosing {node.node_id}!!!\n")

        # check_data
        result = self.check_data(node)

        # in spec case
        if result == "in_spec":
            return False

        # bad data case
        recalibrated = []
        if result == "bad_data":
            recalibrated = [self.diagnose(n) for n in self.dependents(node)]
            print(f"Dependencies diagnoses of {node.node_id}: {recalibrated}\n")
        if recalibrated != [] and not any(recalibrated):
            print(f"{node.node_id} diagnose: False\n")
            return False

        # calibrate
        self.calibrate(node)

        # GALADRIEL: uncomment when platform is connected
        self.update_parameters(node=node)

        print(f"{node.node_id} diagnose: True\n")
        return True

    def check_state(self, node: MinCalibrationNode) -> bool:
        """
        Check if the node's parameters drift timeouts have passed since the last calibration or data validation (a call of check_data).
        These timeouts represent how long it usually takes for the parameters to drift, specified by the user.
        
        Conditions for check state to pass:
            - The cal has had check data or calibrate pass within the timeout period.
            - The cal has not failed calibrate without resolution.
            - No dependencies have been recalibrated since the last time check data or calibrate was run on this cal
            - All dependencies pass check state

        Args:
            node: The node whose parameters need to be checked.

        Returns:
            bool: True if the parameter's drift timeout has not yet expired, False otherwise.
        """
        print(f'Checking state of node "{node.node_id}"\n')

        ### WE THINK WE CAN COMMENT THIS AND THE ALGORITHM WILL GO QUICKER, WITHOUT LOSSING ANYTHING !!!
        ### SINCE EVERY TIME YOU CHECK_STATE YOU COME FROM THE PREVIOUS DEPENDENCES !!!
        # Get dependencies status, all of the dependancies should return True.
        # dependencies_status = [self.check_state(n) for n in self.dependents(node)]
        # print(f"Dependencies status of {node.node_id}: {dependencies_status}\n")

        # Get the list of the dependencies that have been calibrated before this node, all of them should be True
        dependencies_timestamps_previous = [
            n.previous_timestamp < node.previous_timestamp for n in self.dependents(node)
        ]
        # Check if something hapened and the timestamp could not be setted properly and the rest of conditions
        if node.previous_timestamp is None or not all(
            dependencies_timestamps_previous
        ):  # or not all(dependencies_status)
            print(f"check_state of {node.node_id} with False!!! \n")
            return False
        print(
            f"check_state of {node.node_id} with {not is_timeout_expired(node.previous_timestamp, node.drift_timeout)}!!! \n"
        )
        return not is_timeout_expired(node.previous_timestamp, node.drift_timeout)

    def check_data(self, node: MinCalibrationNode) -> str:
        """
        Check if the parameters found in the last calibration are still valid. To do this, this function runs the experiment only in a few
        points, randomly chosen within the sweep interval, and compares the results with the data obtained in the same points whe the
        experiment was last run on the entire sweep interval (full calibration).

        Args:
            node: The node whose parameters need to be checked.

        Returns:
            str: Based on how the experiment results compare with the results obtained during the last full calibration, the function will return

                - "in_spec" if the results are similar. Similarity is determined using the `check_data_confidence_level` argument of the :obj:`~automatic_calibration.CalibrationNode`.
                - "out_of_spec" if the results are not similar enough.
                - "bad_data" if the results are not similar and they don't even fit the model that is expected for this data. The model that the data should fit is indicated
                        by the `fitting_model` attribute of :obj:`~automatic_calibration.CalibrationNode`, and to decide if the data fits the model well enough the r-squared
                        parameter of the fit is used. The tolerance for the r-squared is indicated in the `r_squared_threshold` attribute of :obj:`~automatic_calibration.CalibrationNode`.
                See the source code for details on how these metrics are used to decide what string to return.
        """

        print(f'Checking data of node "{node.node_id}"\n')
        timestamp = node.run_notebook(check=True)

        # Comparison and obtained parameters:
        comparison_outputs = node.previous_output_parameters
        obtained_outputs = node.output_parameters
        
        if comparison_outputs is not None and obtained_outputs is not None: #obtained_outputs will never be None, since we just run the notebook.
            
            # Get params from last notebook
            comparison_params = comparison_outputs["check_parameters"]

            # Get obtained parameters:
            obtained_params = obtained_outputs["check_parameters"]
            
            
            if self.obtained_comparison_error(obtained_params, comparison_params, method=normalized_root_mean_square_error) >= node.in_spec_threshold:
                print(f"check_data of {node.node_id}: in_spec!!!\n")
                node.add_string_to_checked_nb_name("in_spec", timestamp)
                return "in_spec"

            elif self.obtained_comparison_error(obtained_params, comparison_params, method=normalized_root_mean_square_error) >= node.bad_data_threshold:
                print(f"check_data of {node.node_id}: out_of_spec!!!\n")
                node.add_string_to_checked_nb_name("out_spec", timestamp)
                return "out_spec"

        print(f"check_data of {node.node_id}: bad_data!!!\n")
        node.add_string_to_checked_nb_name("bad_data", timestamp)
        return "bad_data"

    def calibrate(self, node: MinCalibrationNode) -> None:
        """
        Run a node's calibration experiment on its default interval of sweep values.

        Args:
            node (CalibrationNode): The node where the calibration experiment is run.
        """
        print(f'Calibrating node "{node.node_id}"\n')
        node.previous_timestamp = node.run_notebook()
        node.add_string_to_checked_nb_name("calibrated", node.previous_timestamp)

    def update_parameters(self, node: MinCalibrationNode) -> None:
        """Update a parameter value in the platform.
        If the node does not have an associated parameter, or the parameter attribute of the node is None,
        this function does nothing. That is because some nodes, such as those associated with the AllXY
        experiment, don't compute the value of a parameter.

        Args:
            node (CalibrationNode): The node that contains the experiment that gives the optimal value of the parameter.
            parameter_value (float | bool | str): The optimal value of the parameter found by the experiment.
        """
        if node.output_parameters is not None and "platform_params" in node.output_parameters:
            for bus_alias, param_name, param_value in node.output_parameters["platform_params"]:
                print(f"Platform updated with: ({bus_alias}, {param_name}, {param_value})")
                # self.platform.set_parameter(alias=bus_alias, parameter=param_name, value=param_value)

            # TODO: Solve the platform serialization problem to descomment this!!!
            # save_platform(self.runcard, self.platform)

    def dependents(self, node: MinCalibrationNode) -> list:
        """Find the nodes that a node depends on.
        In this graph, if an edge goes from node A to node B, then node A depends on node B. Thus the nodes that A depends on are its successors.

        Args:
            node (CalibrationNode): The nodes of which we need the dependencies
 
        Returns:
            list: The nodes that the argument node depends on
        """
        return [self.node_sequence[node_name] for node_name in self.calibration_graph.successors(node.node_id)]

    @staticmethod
    def obtained_comparison_error(obtained: dict[str, list], comparison: dict[str, list], method: Callable) -> float:
        """Returns the error, given the chosen method, between the comparison and obtained samples.

        Args:
            obtained (dict): obtained samples to compare.
            comparison (dict): previous samples to compare.

        Returns:
            float: difference/error between the two samples.
         """
        return method(obtained, comparison)
    