# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Automatic-calibration Controller module, which works with notebooks as nodes."""
from datetime import datetime, timedelta

import networkx as nx

from qililab.automatic_calibration.calibration_node import CalibrationNode
from qililab.data_management import build_platform, save_platform
from qililab.platform.platform import Platform


class CalibrationController:
    """Class that controls the automatic calibration sequence.

    Args:
        calibration_graph (nx.DiGraph): The calibration graph. This is a directed acyclic graph where each node is a string.
        node_sequence (dict[str, CalibrationNode]): Mapping for the nodes of the graph, from strings into the actual initialized nodes.
        runcard (str): The runcard path, containing the serialized platform where the experiments will be run.

    Examples:
        In this example, you will create 2 nodes, and pass them to a :class:`.CalibrationController`, in order to run the maintain algorithm on the second one:

        .. code-block:: python

            personalized_sweep_interval = {
                "start": 10,
                "stop": 50,
                "step": 2,
            }

            # CREATE NODES :
            first = CalibrationNode(
                nb_path="notebooks/first.ipynb",
                in_spec_threshold=4,
                bad_data_threshold=8,
                comparison_model=norm_root_mean_sqrt_error,
                drift_timeout=1800.0,
            )
            second = CalibrationNode(
                nb_path="notebooks/second.ipynb",
                in_spec_threshold=2,
                bad_data_threshold=4,
                comparison_model=norm_root_mean_sqrt_error,
                drift_timeout=1.0,
                sweep_interval=personalized_sweep_interval,
            )

            # NODE MAPPING TO THE GRAPH (key = name in graph, value = node object):
            nodes = {"first": first, "second": second}

            # GRAPH CREATION:
            G = nx.DiGraph()
            G.add_edge("second", "first")

            # CREATE CALIBRATION CONTROLLER:
            controller = CalibrationController(node_sequence=nodes, calibration_graph=G, runcard=path_runcard)

            ### EXECUTIONS TO DO:
            controller.maintain(third)

        .. note::

            Find information about how these nodes and their notebooks need to be in the :class:`CalibrationNode` class documentation.
    """

    def __init__(self, calibration_graph: nx.DiGraph, node_sequence: dict[str, CalibrationNode], runcard: str):
        if not nx.is_directed_acyclic_graph(calibration_graph):
            raise ValueError("The calibration graph must be a Directed Acyclic Graph (DAG).")

        self.calibration_graph: nx.DiGraph = calibration_graph
        """The calibration graph. This is a directed acyclic graph where each node is a string."""

        self.node_sequence: dict[str, CalibrationNode] = node_sequence
        """Mapping for the nodes of the graph, from strings into the actual initialized nodes."""

        self.runcard: str = runcard
        """The runcard path, containing the serialized platform where the experiments will be run."""

        self.platform: Platform = build_platform(runcard)
        """The initialized platform, where the experiments will be run."""

    def run_automatic_calibration(self) -> dict[str, dict]:
        """Run the automatic calibration procedure and retrieve the final set parameters and achieved fidelities dictionaries.

        Returns:
            dict[str, dict]: Dictionary for the last set parameters and the last achieved fidelities. It contains two dictionaries in the keys:
                - "set_parameters"
                - "fidelities"
            The two dictionaries have the following structure:


            Fidelities dictionary (dict[str, tuple]): key being the fidelity name (str), and the value being a tuple that contains in this order:
                - (float) value of fidelity.
                - (str) node_id where this fidelity was computed.
                - (datetime) updated time of the fidelity.

            Set parameters dictionary (dict[tuple, tuple]): key being a tuple containing:
                - (str) the the parameter name.
                - (str) the bus alias where its been set.
            and the dict value being a tuple that contains in this order:
                - (float) value of parameter.
                - (str) node_id where this parameter was computed.
                - (datetime) updated time of the parameter.
        """
        highest_level_nodes = [node for node, in_degree in self.calibration_graph.in_degree() if in_degree == 0]

        for n in highest_level_nodes:
            self.maintain(self.node_sequence[n])

        print(
            "#############################################\n"
            "Automatic calibration completed successfully!\n"
            "#############################################\n"
        )

        return {"set_parameters": self.get_last_set_parameters(), "fidelities": self.get_last_fidelities()}

    def maintain(self, node: CalibrationNode) -> None:
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
        for n in self._dependents(node):
            print(f"maintaining {n.node_id} from maintain({node.node_id})!!!\n")
            self.maintain(n)

        if self.check_state(node):
            return

        result = self.check_data(node)
        if result == "in_spec":
            return
        if result == "bad_data":
            for n in self._dependents(node):
                print(f"diagnosing {n.node_id} from maintain({node.node_id})!!!\n")
                self.diagnose(n)

        # calibrate
        self.calibrate(node)

        # GALADRIEL: uncomment when platform is connected
        self._update_parameters(node)

    def diagnose(self, node: CalibrationNode) -> bool:
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
            recalibrated = [self.diagnose(n) for n in self._dependents(node)]
            print(f"Dependencies diagnoses of {node.node_id}: {recalibrated}\n")
        # If not empty and only filled with False's (not any True).
        if recalibrated != [] and not any(recalibrated):
            print(f"{node.node_id} diagnose: False\n")
            return False

        # calibrate
        self.calibrate(node)

        # GALADRIEL: uncomment when platform is connected
        self._update_parameters(node)

        print(f"{node.node_id} diagnose: True\n")
        return True

    def check_state(self, node: CalibrationNode) -> bool:
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
            n.previous_timestamp < node.previous_timestamp for n in self._dependents(node)
        ]
        # Check if something hapened and the timestamp could not be setted properly and the rest of conditions
        if node.previous_timestamp is None or not all(
            dependencies_timestamps_previous
        ):  # or not all(dependencies_status)
            print(f"check_state of {node.node_id} with False!!! \n")
            return False
        print(
            f"check_state of {node.node_id} with {not self._is_timeout_expired(node.previous_timestamp, node.drift_timeout)}!!! \n"
        )
        return not self._is_timeout_expired(node.previous_timestamp, node.drift_timeout)

    def check_data(self, node: CalibrationNode) -> str:
        """
        Check if the parameters found in the last calibration are still valid. To do this, this function runs the experiment only in a few
        points, randomly chosen within the sweep interval, and compares the results with the data obtained in the same points whe the
        experiment was last run on the entire sweep interval (full calibration).

        Args:
            node: The node whose parameters need to be checked.

        Returns:
            str: Three possible few words description, of how the experiment results compare with the results obtained during the last full calibration.

            Concretely, depending on the provided threshold and comparison method, it will return:
                - "in_spec" if the results are similar. Similarity is determined using the `check_data_confidence_level` argument of the :obj:`~automatic_calibration.CalibrationNode`.
                - "out_of_spec" if the results are not similar enough, but close.
                - "bad_data" if the results are not closely similar.

                The comparison used is indicated by the `comparison_model` attribute of :obj:`~automatic_calibration.CalibrationNode`, which decides if the data fits the model well enough.
                The tolerances for the comparison is indicated in the `in_spec_threshold` and `bad_data_threshold` attributes of :obj:`~automatic_calibration.CalibrationNode`.

            See the source code for details on how these metrics are used to decide what string to return.
        """

        print(f'Checking data of node "{node.node_id}"\n')
        timestamp = node.run_notebook(check=True)

        # Comparison and obtained parameters:
        comparison_outputs = node.previous_output_parameters
        obtained_outputs = node.output_parameters

        if (
            comparison_outputs is not None and obtained_outputs is not None
        ):  # obtained_outputs will never be None, since we just run the notebook.
            # Get params from last notebook
            compar_params = comparison_outputs["check_parameters"]

            # Get obtained parameters:
            obtain_params = obtained_outputs["check_parameters"]

            print("The obtained results are:")
            print("y:", obtain_params["y"])
            print("x:", obtain_params["x"])
            print("The comparison results are:")
            print("y:", compar_params["y"])
            print("x:", compar_params["x"])

            if self._obtain_comparison(node, obtain_params, compar_params) <= node.in_spec_threshold:
                print(f"check_data of {node.node_id}: in_spec!!!\n")
                node.add_string_to_checked_nb_name("in_spec", timestamp)
                node.invert_output_and_previous_output()
                return "in_spec"

            if self._obtain_comparison(node, obtain_params, compar_params) <= node.bad_data_threshold:
                print(f"check_data of {node.node_id}: out_of_spec!!!\n")
                node.add_string_to_checked_nb_name("out_spec", timestamp)
                node.invert_output_and_previous_output()
                return "out_spec"

        print(f"check_data of {node.node_id}: bad_data!!!\n")
        node.add_string_to_checked_nb_name("bad_data", timestamp)
        node.invert_output_and_previous_output()
        return "bad_data"

    def calibrate(self, node: CalibrationNode) -> None:
        """
        Run a node's calibration experiment on its default interval of sweep values.

        Args:
            node (CalibrationNode): The node where the calibration experiment is run.
        """
        print(f'Calibrating node "{node.node_id}"\n')
        node.previous_timestamp = node.run_notebook()
        node.add_string_to_checked_nb_name("calibrated", node.previous_timestamp)

    def _update_parameters(self, node: CalibrationNode) -> None:
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
                self.platform.set_parameter(alias=bus_alias, parameter=param_name, value=param_value)

            save_platform(self.runcard, self.platform)

    def get_last_set_parameters(self) -> dict[tuple, tuple]:
        """Retrieve the last set parameters of the graph.

        Returns:
            dict[tuple, tuple]: Set parameters dictionary, with the dict key being a tuple containing:
                - (str) the the parameter name.
                - (str) the bus alias where its been set.
            and the dict value being a tuple that contains in this order:
                - (float) value of parameter.
                - (str) node_id where this parameter was computed.
                - (datetime) updated time of the parameter.
        """
        parameters: dict[tuple, tuple] = {}
        print("LAST SET PARAMETERS:")
        for node in self.node_sequence.values():
            if (
                node.output_parameters is not None
                and node.previous_timestamp is not None
                and "platform_params" in node.output_parameters
            ):
                for bus, parameter, value in node.output_parameters["platform_params"]:
                    print(
                        f"Last set {parameter} in bus {bus}: {value} (updated in {node.node_id} at {datetime.fromtimestamp(node.previous_timestamp)})"
                    )
                    parameters[(parameter, bus)] = (
                        value,
                        node.node_id,
                        datetime.fromtimestamp(node.previous_timestamp),
                    )

        return parameters

    def get_last_fidelities(self) -> dict[str, tuple]:
        """Retrieve the last updated fidelities of the graph.

        Returns:
            dict[str, tuple]: Fidelities dictionary, with key being the fidelity name (str), and the value being a tuple that contains in this order:
                - (float) value of fidelity.
                - (str) node_id where this fidelity was computed.
                - (datetime) updated time of the fidelity.
        """
        fidelities: dict[str, tuple] = {}
        print("LAST RETRIEVED FIDELITIES:")
        for node in self.node_sequence.values():
            if (
                node.output_parameters is not None
                and node.previous_timestamp is not None
                and "fidelities" in node.output_parameters
            ):
                for fidelity, value in node.output_parameters["fidelities"].items():
                    print(
                        f"Last fidelity of {fidelity}: {value} (updated in {node.node_id} at {datetime.fromtimestamp(node.previous_timestamp)})"
                    )
                    fidelities[fidelity] = (value, node.node_id, datetime.fromtimestamp(node.previous_timestamp))

        return fidelities

    def _dependents(self, node: CalibrationNode) -> list:
        """Find the nodes that a node depends on.
        In this graph, if an edge goes from node A to node B, then node A depends on node B. Thus the nodes that A depends on are its successors.

        Args:
            node (CalibrationNode): The nodes of which we need the dependencies

        Returns:
            list: The nodes that the argument node depends on
        """
        return [self.node_sequence[node_name] for node_name in self.calibration_graph.successors(node.node_id)]

    @staticmethod
    def _obtain_comparison(node: CalibrationNode, obtained: dict[str, list], comparison: dict[str, list]) -> float:
        """Returns the error, given the chosen method, between the comparison and obtained samples.

        Args:
            obtained (dict): obtained samples to compare.
            comparison (dict): previous samples to compare.

        Returns:
            float: difference/error between the two samples.
        """
        return node.comparison_model(obtained, comparison)

    @staticmethod
    def _is_timeout_expired(timestamp: float, timeout: float) -> bool:
        """
        Check if the time passed since the timestamp is greater than the timeout duration.

        Args:
            timestamp (float): Timestamp from which the time should be checked, described in UNIX timestamp format.
            timeout (float): The timeout duration in seconds.

        Returns:
            bool: True if the timeout has expired, False otherwise.
        """
        # Convert the timestamp and timeout to datetime objects
        timestamp_dt = datetime.fromtimestamp(timestamp)
        timeout_duration = timedelta(seconds=timeout)

        # Get the current time
        current_time = datetime.now()

        # Calculate the time that should have passed (timestamp + timeout duration)
        timeout_time = timestamp_dt + timeout_duration

        # Check if the current time is greater than the timeout time
        return current_time > timeout_time
