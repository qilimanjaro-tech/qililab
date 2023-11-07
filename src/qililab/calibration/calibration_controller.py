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

from qililab.calibration.calibration_node import CalibrationNode
from qililab.config import logger
from qililab.data_management import build_platform, save_platform
from qililab.platform.platform import Platform


class CalibrationController:
    """Controls the automatic calibration sequence.

    **Usage:**
        - To calibrate the full graph, use the ``run_automatic_calibration()`` method.
        - To target and ensure a node works, use the ``maintain(node)`` method.

    |

    **Graph Structure:**

    In the graph, directions should be given by `nodes` pointing to their next `dependents` (natural time flow for calibration).
    This defines our `starts` and `ends` of the calibration:

    - `starts`: `Roots` (``in_degree=0``, no arrows pointing in, no `dependencies`) of the graph, where all arrows leave the node.

    - `ends`: `Leaves` (``out_degree=0``, no arrows pointing out, no `dependants`) of the graph, where all arrows enter the node.

    .. code-block:: python

        #                     /--> 2 -->\\
        #                    /     |     \\
        #    (start, root)  0      |      3 --> 4 (end, leave)
        #                    \     v     /
        #                     \--> 1 -->/

    |

    **Calibration Workflow:**

    The calibration process is structured into three levels of methods:

        1. **Highest Level Method**: The ``run_automatic_calibration()`` method finds all the end nodes of the graph (`leaves`, those without further `dependents`) and runs ``maintain()`` on them.

        2. **Mid-Level Methods**: ``maintain()`` and ``diagnose()``.
            - ``maintain(node)`` starts from the `roots` that ``node`` depends on, and moves forwards (`dependency -> dependant`) until ``node``, checking the last time executions and data at each step. If a problem (``bad_data``) is found, it calls ``diagnose()`` to solve it.
            - ``diagnose(node)`` does more strict checks, fixing inaccuracies in the system's state to allow ``maintain()`` to continue. It works in reverse, starting from the problematic (``bad_data``) node, it goes back (`dependency <- dependant`) until it finds the origin of the problem.

        3. **Low-Level Methods**: ``check_state()``, ``check_data()``, and ``calibrate()`` are the methods you would be calling during this process to interact with the ``nodes``.

    Finally, ``run_automatic_calibration()`` is designed to start acquiring data or calibrating in the optimal location of the graph to avoid extra work:

    - If node A has been calibrated very recently (before the ``drift_timeout`` of the :class:`.CalibrationNode`), it would be a waste of resources to check its data, so ``check_state()`` makes ``maintain()`` skip it.
    - If node A depends on node B, before calibrating node A, we check the data of node B. Calibrating A would be a waste of resources if we were doing so based on faulty data, so it goes to its dependencies first.

    |

    **Dangerous Behaviors:**

    Note that depending on your ``CalibrationController`` construction, you can have dangerous behaviors in the workflow. You need to watch out for:

    - If you give bad ``comparison_thresholds`` or have bad ``comparison_models``, returning ``out_of_spec`` when you actually have ``bad_data`` or the other way around, will make ``diagnose()`` not being able to work properly, since for it to work, you need to have a single layer node separation (``out_of_spec``) between the ``in_spec`` and the ``bad_data`` nodes.
    - If you give too long ``drift_timeout``'s, since ``maintain()`` will assume the node is 100% working, you will go to further dependents when maybe you shouldn't without recalibrating. In the end ``diagnose()`` saves the day here, since it doesn't do ``check_state()``, although it will be less efficient.

    .. note:: Find more information about the automatic calibration workflow at https://arxiv.org/abs/1803.03226.

    Args:
        calibration_graph (nx.DiGraph): The calibration (directed acyclic) graph, where each node is a ``string`` corresponding to a ``CalibrationNode.node_id``. Directions should be given
            by `nodes` pointing to their next `dependents` (natural time flow for calibration), defining our `starts` and `ends` of the calibration as the `roots` (``in_degree=0``) and `leaves`
            (``out_degree=0``) of the graph.
        node_sequence (dict[str, CalibrationNode]): Mapping for the nodes of the graph, from strings into the actual initialized nodes.
        runcard (str): The runcard path, containing the serialized platform where the experiments will be run.
    
    Examples:
        This example shows how to create 2 nodes twice, one for each qubit, and pass them to a :class:`.CalibrationController` to run the ``maintain()`` algorithm on the second one.

        .. code-block:: python
            import numpy as np
            sweep_interval = np.arange(start=0, stop=19, step=1)
            # GRAPH CREATION AND NODE MAPPING (key = name in graph, value = node object):
            nodes = {}
            G = nx.DiGraph()

            # CREATE NODES:
            for qubit in [0, 1]:
                first = CalibrationNode(
                    nb_path="notebooks/first.ipynb",
                    qubit_index=qubit,
                    in_spec_threshold=4,
                    bad_data_threshold=8,
                    comparison_model=norm_root_mean_sqrt_error,
                    drift_timeout=1800.0,
                )
                nodes[first.node_id] = first
                second = CalibrationNode(
                    nb_path="notebooks/second.ipynb",
                    qubit_index=qubit,
                    in_spec_threshold=2,
                    bad_data_threshold=4,
                    comparison_model=norm_root_mean_sqrt_error,
                    drift_timeout=1.0,
                    sweep_interval=sweep_interval,
                )
                nodes[second.node_id] = second
                # GRAPH BUILDING:
                G.add_edge(second.node_id, first.node_id)
            # CREATE CALIBRATION CONTROLLER:
            controller = CalibrationController(node_sequence=nodes, calibration_graph=G, runcard=path_runcard)
            ### EXECUTIONS TO DO:
            controller.maintain(second)
        .. note::
            Find information about how these nodes and their notebooks need to be in the :class:`CalibrationNode` class documentation.
    """

    def __init__(self, calibration_graph: nx.DiGraph, node_sequence: dict[str, CalibrationNode], runcard: str):
        if not nx.is_directed_acyclic_graph(calibration_graph):
            raise ValueError("The calibration graph must be a Directed Acyclic Graph (DAG).")

        self.calibration_graph: nx.DiGraph = calibration_graph
        """The calibration (directed acyclic) graph. Where each node is a ``string`` corresponding to a ``CalibrationNode.node_id``.

        Directions should be given by `nodes` pointing to their next `dependents` (natural time flow for calibration),
        defining our `starts` and `ends` of the calibration, as:

        - `starts`: `roots` (``in_degree=0``, no arrows pointing in, no `dependencies`) of the graph, where all arrows leave the node.

        - `ends`: `leaves` (``out_degree=0``, no arrows pointing out, no `dependants`) of the graph, where all arrows enter the node.

        .. code-block:: python

            #                     /--> 2 -->\\
            #                    /     |     \\
            #    (start, root)  0      |      3 --> 4 (end, leave)
            #                    \     v     /
            #                     \--> 1 -->/
        """

        self.node_sequence: dict[str, CalibrationNode] = node_sequence
        """Mapping for the nodes of the graph, from strings into the actual initialized nodes."""

        self.runcard: str = runcard
        """The runcard path, containing the serialized platform where the experiments will be run."""

        self.platform: Platform = build_platform(runcard)
        """The initialized platform, where the experiments will be run."""

    def run_automatic_calibration(
        self, force_maintain_timeout_ratio: float = 0.0, safe_diagnose: bool = False
    ) -> dict[str, dict]:
        """Runs the full automatic calibration procedure and retrieve the final set parameters and achieved fidelities dictionaries.
        This is primary interface for our calibration procedure and it's the highest level algorithm.
        
        The method performs a call to `maintain` for all nodes with no dependants (nodes with zero in-degree in the calibration grah).
        
        The calls to mainain can skip the `check_status` method if they are forced, the flag `force_maintain` is computed based on the conditions of mentioned nodes,
        the computation of this condition is performed by the method CalibrationController._get_forced_maintain_condition().

        This is the primary interface for our calibration procedure and the highest level algorithm, which finds all the end nodes of the graph
        (`leaves`, those without further `dependents`) and runs ``maintain()`` on them.
        
        # TODO: explain, the two new arguments
        
        Args:
            force_maintain_timeout_ratio (float, optional): Argument needed to compute the force maintain condition. Defaults to 0.0.
            safe_diagnose (bool, optional): Flag to specify if we make sure to avoid corner cases while diagnosing (its slower). Defaults to False.

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
            force_mantain = CalibrationController._get_forced_maintain_condition(n, force_maintain_timeout_ratio)
            self.maintain(self.node_sequence[n], force_mantain=force_mantain, safe_diagnose=safe_diagnose)

        logger.info(
            "#############################################\n"
            "Automatic calibration completed successfully!\n"
            "#############################################\n"
        )

        return {"set_parameters": self.get_last_set_parameters(), "fidelities": self.get_last_fidelities()}

    def maintain(self, node: CalibrationNode, force_mantain: bool = False, safe_diagnose: bool = False) -> None:
        """Calls all the necessary subroutines in the respective dependencies to get a node in spec. Maintain contains the main workflow for
        our calibration procedure, and it's what is called from ``run_automatic_calibration()`` into each of the final nodes of our graph.
        
        It is designed to start actually acquiring data (by calling 'check_data' or 'calibrate') in the optimal location
        of the graph, to avoid extra work: for example if node A depends on node B, before trying to calibrate node A we check
        the state of node B. If node B is out of spec or has bad data, calibrating A will be a waste of resource because we
        will be doing so based on faulty data.
        
        The algorithm goes back to the start of all the nodes dependencies, and working from them up, checking their last time executions
        and their data, searching for problematic cases. In such cases, depending on the severity, ``maintain()`` would directly calibrate
        or call the other mid-level method, ``diagnose()``, which is responsible for working in reverse, from the problematic one, going
        down to all their dependencies, until finds the root of the problem, then passes such information back to the ``maintain()``
        method, so it can calibrate accordingly, and finish its job.
        
        Finally, during all this process, the mid-level methods would be calling these low-level methods, that act on the nodes:
        ``calibrate()``, ``check_status()`` and ``check_data()``.
        
        # TODO: explain the new parameters flow.

        Args:
            node (CalibrationNode): The node where we want to start the algorithm on, getting it in spec. Normally you would want
                this node to be the furthest node in the calibration graph.
            force_mantain (bool, optional): Flag to force the method to not considerate `check_status` output value,
                meaning it allways perform a call to `check_data`. Default to False.
            safe_diagnose (bool, optional): Flag to specify if we make sure to avoid corner cases while diagnosing (its slower). Defaults to False.
        """
        logger.info("Maintaining %s.\n", node.node_id)
        # Recursion over all the nodes that the current node depends on.
        for n in self._dependencies(node):
            logger.info("Maintaining %s from maintain(%s).\n", n.node_id, node.node_id)
            self.maintain(n)

        node_status = self.check_state(node)
        if not force_mantain and node_status:
            return

        result = self.check_data(node)
        if result == "in_spec":
            return
        if result == "bad_data":
            for n in self._dependents(node):
                logger.info("Diagnosing %s from maintain(%s).\n", n.node_id, node.node_id)
                self.diagnose(n, safe_diagnose)

        # implicit out_spec case
        if force_mantain and node_status:
            logger.info(
                "Force maintaining node %s. `Check satus` has passed but the real state of the node was not `in_spec', perhaps drift timeouts shall be updated.",
                node.node_id,
            )

        # calibrate
        self.calibrate(node)
        self._update_parameters(node)

    def diagnose(self, node: CalibrationNode, safe: bool = False):
        """Checks the data of all the dependencies of a node, until it finds the root of the problem with their data.

        This is a method called by ``maintain()`` in the special case that its call of ``check_data()`` finds bad data.

        ``Diagnose()`` workflow works in reverse, starting from the problematic (``bad_data``) node, it goes back (`dependency <- dependant`)
        until it finds the origin of the problem (the first and only ``out_of_spec`` of that path, since the previous will be ``in_spec`` and the
        followings in ``bad_data``).

        ``Maintain()`` assumes that our knowledge of the state of the system matches the actual state of the system: if we knew a node would
        return bad data, we wouldn't bother ``calibrating`` it. The fact that ``check_data()`` returns ``bad_data`` means that that's not the
        case, our knowledge of the systems's state is inaccurate. That why ``diagnose()`` does more strict checks, fixing inaccuracies in our
        knowledge of the system's state, to allow ``maintain()`` to continue.

        Finally mention, two important thing to have in mind:

        - if you give bad ``comparison_thresholds`` or have bad ``comparison_models``, which return ``out_of_spec`` when you actually have ``bad_data`` or the other way around, it will make your full calibration fail. Since for ``diagnose()`` to work, you need to have a single node separation (``out_of_spec``) between the ``in_spec`` and the ``bad_data`` ones.
        - if you have wrong ``drift_timeout``, the algorithm will be slower, but in the end ``diagnose()`` saves the day, achieving the full calibration, since it doesn't do ``check_state()``.
        
        # TODO: explain, the above two statements with the new flag.
        
        Diagnose called with flag `check` will make sure `out_spec` nodes are detected by reliying on actuall information of dependant nodes.
        Otherwise the algorithm will rely on `out_spec` classification method provided by the user via comparison model chosen.
        
        Note that `check` will cover corner cases that may be caused by user choices in exchange for time complexity as the number of
        calls to `check_data` will be higher on average.
        
        .. note:: Find more information about the ``diagnose()`` idea at https://arxiv.org/abs/1803.03226.

        Args:
            node (CalibrationNode): The node where we want to start the algorithm.
            safe (bool, optional):  Flag to specify if we make sure to avoid corner cases (its slower). Defaults to False.

        Returns:
            bool: True is there have been recalibrations, False otherwise. The return value is only used by recursive calls.
        """
        
        logger.info("diagnosing %s.\n", node.node_id)

        if safe:
            # in spec case
            if self.check_data(node) == "in_spec":
                return

            # bad_data/out_spec case
            for n in self._dependents(node):
                self.diagnose(n, safe=True)

            # calibrate
            self.calibrate(node)
            self._update_parameters(node)

        else:
            result = self.check_data(node)

            # in spec case
            if result == "in_spec":
                return False

            # bad data case
            recalibrated = []
            if result == "bad_data":
                recalibrated = [self.diagnose(n) for n in self._dependencies(node)]
                logger.info("Dependencies diagnoses of %s: %s\n", node.node_id, str(recalibrated))
            # If not empty and only filled with False's (not any True).
            if recalibrated != [] and not any(recalibrated):
                return False

            # calibrate
            self.calibrate(node)
            self._update_parameters(node)
            return True

    def check_state(self, node: CalibrationNode) -> bool:
        """Checks if the node's parameters drift timeouts have passed since the last calibration or data validation (a call of check_data).
        These timeouts represent how long it usually takes for the parameters to drift, specified by the user.
        Conditions for check state to pass:
            - The cal has had check data or calibrate pass within the timeout period.
            - The cal has not failed calibrate without resolution.
            - No dependencies have been recalibrated since the last time check data or calibrate was run on this cal
            - All dependencies pass check state

        Args:
            node (CalibrationNode): The node whose state needs to be checked.

        Returns:
            bool: True if the parameter's drift timeout has not yet expired, False otherwise.
        """
        logger.info('Checking state of node "%s".\n', node.node_id)

        # Get the list of the dependencies that have been calibrated before this node, all of them should be True
        dependencies_timestamps_previous = [
            n.previous_timestamp < node.previous_timestamp for n in self._dependencies(node)
        ]
        # Check if something hapened and the timestamp could not be setted properly and the rest of conditions
        if node.previous_timestamp is None or not all(
            dependencies_timestamps_previous
        ):  # or not all(dependencies_status)
            logger.info("check_state of %s: False.\n", node.node_id)
            return False
        logger.info(
            "check_state of %s: %r.\n",
            node.node_id,
            (not self._is_timeout_expired(node.previous_timestamp, node.drift_timeout)),
        )
        return not self._is_timeout_expired(node.previous_timestamp, node.drift_timeout)

    def check_data(self, node: CalibrationNode) -> str:
        """Checks if the parameters found in the last calibration are still valid, doing a reduced execution of the notebook.

        To do this, ``check_data()`` runs the experiment only in a few points, randomly chosen within the ``sweep_interval``,
        and compares the results with the data obtained in the same points when the experiment was last ``calibrate()`` with the
        entire ``sweep_interval``.

        The comparison is done with the model is indicated by the ``comparison_model`` attribute of :class:`.CalibrationNode`,
        which returns a value indicating how well the data fits the model.

        This comparison is then classified as ``in_spec`` (still valid), ``out_of_spec`` (drifted, but close) or ``bad_data``
        (noise/doesn't follow the desired fit, or no previous execution) given the ``in_spec_threshold`` and ``bad_data_threshold``
        attributes of :class:`.CalibrationNode`.

        .. note:: Find more information about the ``check_data()`` idea at https://arxiv.org/abs/1803.03226.

        Args:
            node (CalibrationNode): The node whose parameters need to be checked.

        Returns:
            str: The status of the data, depending on how the current results compare with the obtained during the last full calibration.

            Concretely, depending on the provided thresholds and comparison models, it will return:

            - ``in_spec`` if the results are still acceptable to use.
            - ``out_of_spec`` if the results have drifted are not acceptable enough, but they are close, and still follow the desired fit.
            - ``bad_data`` if the results don't follow the desired fit, or are noisy, which should happen when dependencies have drifted. Or also if there are no previous executions.
        """
        # pylint: disable=protected-access

        logger.info('Checking data of node "%s".\n', node.node_id)
        timestamp = node.run_node(check=True)

        # Comparison and obtained parameters:
        comparison_outputs = node.previous_output_parameters
        obtained_outputs = node.output_parameters

        # If no previous result, return bad_data:
        comparison_result = "bad_data"

        # Do comparison and return the result:
        # (obtained_outputs should never be None, since we just run the notebook)
        if comparison_outputs is not None and obtained_outputs is not None:
            # Get comparison from last notebook and the new obtained parameters.
            compar_params = comparison_outputs["check_parameters"]
            obtain_params = obtained_outputs["check_parameters"]
            logger.info("obtained: %s ", str(obtain_params))
            logger.info("comparison: %s", str(compar_params))

            comparison_number = self._obtain_comparison(node, obtain_params, compar_params)

            if comparison_number <= node.in_spec_threshold:
                comparison_result = "in_spec"

            elif comparison_number <= node.bad_data_threshold:
                comparison_result = "out_of_spec"

        # Do the necessary following changes:
        logger.info("check_data of %s: %s.\n", node.node_id, comparison_result)
        node._add_string_to_checked_nb_name(comparison_result, timestamp)
        node.previous_output_parameters = node.output_parameters
        return comparison_result

    def calibrate(self, node: CalibrationNode) -> None:
        """Runs a node's experiment on its default values of the ``sweep_interval``.

        This method is responsible for calibrating a node to bring it within spec. The calibration process is node-specific
        and depends on the notebook implementation and the calibration parameters.

        .. note:: Find more information about the ``calibrate()`` idea at https://arxiv.org/abs/1803.03226.

        Args:
            node (CalibrationNode): The node where the calibration experiment is run.
        """
        logger.info('Calibrating node "%s".\n', node.node_id)
        node.previous_timestamp = node.run_node()
        node._add_string_to_checked_nb_name("calibrated", node.previous_timestamp)  # pylint: disable=protected-access

    def _update_parameters(self, node: CalibrationNode) -> None:
        """Updates the node parameters value in the platform, after a calibration.

        If the node does not have an associated parameter, or the parameter attribute of the node is None,
        this function does nothing. That is because some nodes, such as those associated with the AllXY
        experiment, don't compute the value of a parameter.

        Args:
            node (CalibrationNode): The node which parameters need to be updated in the platform.
        """
        if node.output_parameters is not None and "platform_params" in node.output_parameters:
            for bus_alias, qubit, param_name, param_value in node.output_parameters["platform_params"]:
                logger.info(
                    "Platform updated with: (bus: %s, q: %d, %s, %f).", bus_alias, qubit, param_name, param_value
                )
                self.platform.set_parameter(alias=bus_alias, parameter=param_name, value=param_value, channel_id=qubit)

            save_platform(self.runcard, self.platform)

    def get_last_set_parameters(self) -> dict[tuple, tuple]:
        """Retrieves the last set parameters of the graph.

        Returns:
            dict[tuple, tuple]: Set parameters dictionary, with the dict key being a tuple containing:
                - (str) the parameter name.
                - (str) the bus alias where its been set.
                - (int) the qubit where its been set.
            and the dict value being a tuple that contains in this order:
                - (float) value of parameter.
                - (str) node_id where this parameter was computed.
                - (datetime) updated time of the parameter.
        """
        parameters: dict[tuple, tuple] = {}
        for node in self.node_sequence.values():
            if (
                node.output_parameters is not None
                and node.previous_timestamp is not None
                and "platform_params" in node.output_parameters
            ):
                for bus, qubit, parameter, value in node.output_parameters["platform_params"]:
                    parameters[(parameter, bus, qubit)] = (
                        value,
                        node.node_id,
                        datetime.fromtimestamp(node.previous_timestamp),
                    )

        return parameters

    def get_last_fidelities(self) -> dict[tuple, tuple]:
        """Retrieves the last updated fidelities of the graph.

        Returns:
            dict[tuple, tuple]: Fidelities dictionary, with the dict key being a tuple containing:
                - (str) the fidelity name.
                - (int) the qubit where its been set.
            and the dict value being a tuple that contains in this order:
                - (float) value of fidelity.
                - (str) node_id where this fidelity was computed.
                - (datetime) updated time of the fidelity.
        """
        fidelities: dict[tuple, tuple] = {}
        for node in self.node_sequence.values():
            if (
                node.output_parameters is not None
                and node.previous_timestamp is not None
                and "fidelities" in node.output_parameters
            ):
                for qubit, fidelity, value in node.output_parameters["fidelities"]:
                    fidelities[(fidelity, qubit)] = (
                        value,
                        node.node_id,
                        datetime.fromtimestamp(node.previous_timestamp),
                    )

        return fidelities

    def _dependencies(self, node: CalibrationNode) -> list:
        """Finds the dependencies of a node.

        If in our graph we have `A -> B`, then node B depends on node A. Thus calling this method on B would return A.

        Args:
            node (CalibrationNode): The nodes for which the dependencies need to be retrieved.

        Returns:
            list: The nodes that the argument node depends on.
        """
        return [self.node_sequence[node_name] for node_name in self.calibration_graph.successors(node.node_id)]

    @staticmethod
    def _obtain_comparison(node: CalibrationNode, obtained: dict[str, list], comparison: dict[str, list]) -> float:
        """Returns the error, given the chosen method, between the comparison and obtained samples.

        Args:
            node (CalibrationNode): node from which the data comparison will be done.
            obtained (dict): obtained samples to compare.
            comparison (dict): previous samples to compare.

        Returns:
            float: difference/error between the two samples.
        """
        return node.comparison_model(obtained, comparison)

    @staticmethod
    def _is_timeout_expired(timestamp: float, timeout: float) -> bool:
        """Checks if the time passed since the timestamp is greater than the timeout duration.
        Args:
            timestamp (float): Timestamp from which the time should be checked, described in UNIX timestamp format.
            timeout (float): The timeout duration in seconds.
        Returns:
            bool: True if the timeout has expired, False otherwise.
        """
        # Calculate the time that should have passed (timestamp + timeout duration), convert them to datetime objects:
        timestamp_dt = datetime.fromtimestamp(timestamp)
        timeout_duration = timedelta(seconds=timeout)
        timeout_time = timestamp_dt + timeout_duration

        # Check if the current time is greater than the timeout time
        current_time = datetime.now()
        return current_time > timeout_time

    @staticmethod
    def _get_forced_maintain_condition(node: CalibrationNode, ratio: float = 0.0) -> bool:
        """Method to return if a Calibration Node should be force maintained or not.
        The condition checks if the time trancurred from the last calibration is greater than a ratio of the drift timeout of the node.

        Args:
            node (CalibrationNode): Calibration Node to get the the forced maintain condition
            ratio(flat, optional): Ratio used for the condition. Default to 0.0.

        Returns:
            bool: Returns True if the condition is met. Otherwise returns False.
        """
        comp = node.drift_timeout * ratio if ratio != 0 else 600
        now = datetime.timestamp(datetime.now())
        return now - node.previous_timestamp > comp if node.previous_timestamp is not None else False
