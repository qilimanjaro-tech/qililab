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

# pylint: disable=anomalous-backslash-in-string, inconsistent-return-statements
"""Automatic-calibration Controller module, which works with notebooks as nodes."""
from datetime import datetime, timedelta

import networkx as nx
import pandas as pd

import qililab as ql
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

    .. note::

        Find information about the automatic-calibration workflow, in the examples below.

    Args:
        calibration_graph (nx.DiGraph): The calibration (directed acyclic) graph, where each node is a ``string`` corresponding to a ``CalibrationNode.node_id``. Directions should be given
            by `nodes` pointing to their next `dependents` (natural time flow for calibration), defining our `starts` and `ends` of the calibration as the `roots` (``in_degree=0``) and `leaves`
            (``out_degree=0``) of the graph.

        node_sequence (dict[str, CalibrationNode]): Mapping for the nodes of the graph, from strings into the actual initialized nodes.
        runcard (str): The runcard path, containing the serialized platform where the experiments will be run.

    Examples:

        **Calibration Workflow:**

        The calibration process is structured into three levels of methods:

        1. **Highest Level Method**: The ``run_automatic_calibration()`` method finds all the end nodes of the graph (`leaves`, those without further `dependents`) and runs ``maintain()`` on them.

        2. **Mid-Level Methods**: ``maintain()`` and ``diagnose()``.
            - ``maintain(node)`` starts from the `roots` that ``node`` depends on, and moves forwards (`dependency -> dependant`) until ``node``, checking the last time executions and data at each step. If a problem (``bad_data``) is found, it calls ``diagnose()`` to solve it.
            - ``diagnose(node)`` does more strict checks, fixing inaccuracies in the system's state to allow ``maintain()`` to continue. It works in reverse, starting from the problematic (``bad_data``) node, it goes back (`dependency <- dependant`) until it finds the origin of the problem.

        3. **Low-Level Methods**: ``check_state()``, ``check_data()``, and ``calibrate()`` are the methods you would be calling during this process to interact with the ``nodes``.

        |

        Finally, ``run_automatic_calibration()`` is designed to start acquiring data or calibrating in the optimal location of the graph to avoid extra work:

        # TODO: Change this workflow explanations to new one
        - If node A has been calibrated very recently (before the ``drift_timeout`` of the :class:`.CalibrationNode`), it would be a waste of resources to check its data, so ``check_state()`` makes ``maintain()`` skip it.
        - If node A depends on node B, before calibrating node A, we check the data of node B. Calibrating A would be a waste of resources if we were doing so based on faulty data, so it goes to its dependencies first.

        .. note:: Find more information about the automatic calibration workflow at https://arxiv.org/abs/1803.03226.

        ----------

        **Dangerous Behaviors:**

        Note that depending on your ``CalibrationController`` construction, you can have dangerous behaviors in the workflow. You need to watch out for:

        # TODO: change this dangerous behaviours explanations, to new workflow
        - If you give bad ``comparison_thresholds`` or have bad ``comparison_models``, returning ``out_of_spec`` when you actually have ``bad_data`` or the other way around, will make ``diagnose()`` not being able to work properly, since for it to work, you need to have a single layer node separation (``out_of_spec``) between the ``in_spec`` and the ``bad_data`` nodes.
        - If you give too long ``drift_timeout``'s, since ``maintain()`` will assume the node is 100% working, you will go to further dependents when maybe you shouldn't without recalibrating. In the end ``diagnose()`` saves the day here, since it doesn't do ``check_state()``, although it will be less efficient.

        ----------

        **Practical example:**

        To create two linked nodes twice, for two different qubits, and pass them to a :class:`.CalibrationController` and run a ``maintain()``, you need:

        .. code-block:: python

            import numpy as np
            import networkx as nx

            from qililab.calibration import CalibrationController, CalibrationNode, norm_root_mean_sqrt_error

            # GRAPH CREATION AND NODE MAPPING (key = name in graph, value = node object):
            nodes = {}
            G = nx.DiGraph()
            first, second = [], []

            # CREATE NODES:
            for qubit in [0, 1]:
                first[qubit] = CalibrationNode(
                    nb_path="notebooks/first.ipynb",
                    qubit_index=qubit,
                    in_spec_threshold=4,
                    bad_data_threshold=8,
                    comparison_model=norm_root_mean_sqrt_error,
                    drift_timeout=1800.0,
                )
                nodes[first[qubit].node_id] = first[qubit]

                second[qubit] = CalibrationNode(
                    nb_path="notebooks/second.ipynb",
                    qubit_index=qubit,
                    in_spec_threshold=2,
                    bad_data_threshold=4,
                    comparison_model=norm_root_mean_sqrt_error,
                    drift_timeout=1.0,
                    sweep_interval=np.arange(start=0, stop=19, step=1),
                )
                nodes[second[qubit].node_id] = second[qubit]

                # GRAPH BUILDING (1 --> 2):
                G.add_edge(first[qubit].node_id, second[qubit].node_id)

            # CREATE CALIBRATION CONTROLLER:
            controller = CalibrationController(node_sequence=nodes, calibration_graph=G, runcard=path_runcard)

            ### WORKFLOW TO DO:
            controller.maintain(second[1]) # maintain second node for qubit 1

        .. note::

            Find information about how these nodes and their notebooks need to be in the :class:`CalibrationNode` class documentation.

            There you will also find the above code, but without defining ``first`` and ``second`` as lists.
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
        """Mapping for the nodes of the graph, from strings into the actual initialized nodes (dict)."""

        self.runcard: str = runcard
        """The runcard path, containing the serialized platform where the experiments will be run (str)."""

        self.platform: Platform = build_platform(runcard)
        """The initialized platform, where the experiments will be run (Platform)."""

    def calibrate_all(self, node: CalibrationNode):
        """Calibrates all the nodes sequentially.

        Args:
            node (CalibrationNode): The node where we want to start the `calibration_all()` on. Normally you would want
                this node to be the furthest node in the calibration graph.
        """
        logger.info("WORKFLOW: Calibrating all %s.\n", node.node_id)
        for n in self._dependencies(node):
            self.calibrate_all(n)

        # You can skip it from 2h time, but also skip it due to `been_calibrated()`
        # TODO: DOCUMENT: If you want to start the calibration from the start again, just remove the executed files!
        if (
            node.previous_timestamp is None or self._is_timeout_expired(node.previous_timestamp, 7200.0)
        ) and not node.been_calibrated:
            self.calibrate(node)
            self._update_parameters(node)

    def run_automatic_calibration(
        self,
        force_maintain: bool = False,
        safe_diagnose: bool = True,
        strict_dependencies: bool = False,
        run_fidelities: bool = False,
        calibrate_all: bool = False,
    ) -> dict[str, dict]:
        """Runs the full automatic calibration procedure and retrieves the final set parameters and achieved fidelities dictionaries.

        This is the primary interface for our calibration procedure and the highest level algorithm, which finds all the end nodes of the graph
        (`leaves`, those without further `dependents`) and runs ``maintain()`` on them.

        Args:
            force_maintain_timeout_ratio (float, optional): Argument needed to compute the force maintain condition. Defaults to 0.0.
            safe_diagnose (bool, optional): Flag to specify if we make sure to avoid corner cases while diagnosing (its slower). Defaults to False.
            strict_dependencies (bool, optional): Flag to specify if the drift_timeout dependencies should be completely strict, meaning that a previous
                dependency can never have a smaller drift_timeout. Defaults to False.

        Returns:
            dict[str, dict]: Dictionary for the last set parameters and the last achieved fidelities. It contains two dictionaries (dict[tuple, tuple]) in the keys:
                - "set_parameters": Set parameters dictionary, with the key and values being tuples containing, in this order:
                    - key: (``str``: parameter name, ``str``: bus alias, int: qubit).
                    - value: (``float``: parameter value, ``str``: ``node_id`` where computed, ``datetime``: updated time).

                - "fidelities": Fidelities dictionary, with the key and values being tuples containing, in this order:
                    - key: (``str``: parameter name, ``int``: qubit).
                    - value: (``float``: parameter value, ``str``: node_id where computed, ``datetime``: updated time).
        """
        highest_level_nodes = [
            self.node_sequence[node]
            for node, out_degree in self.calibration_graph.out_degree()
            if (out_degree == 0 and not self.node_sequence[node].fidelity)
        ]

        # TODO: Do a couple of integrations test, with deterministic scripts, where you know the sequence of check_datas and
        # TODO: calibrates the workflow would need to follow, like the ones in my notebook, and check them.

        for node in highest_level_nodes:
            if calibrate_all:
                self.calibrate_all(node)

            else:
                self.maintain(
                    node,
                    force_mantain=force_maintain,
                    safe_diagnose=safe_diagnose,
                    strict_dependencies=strict_dependencies,
                )

        if run_fidelities:
            self.run_fidelities()

        logger.info(
            "\n#############################################\n"
            "Automatic calibration completed successfully!\n"
            "#############################################\n"
        )
        return self.get_qubit_fidelities_and_parameters_df_tables()

    def get_qubit_fidelities_and_parameters_df_tables(self) -> dict[str, pd.DataFrame]:
        """Generates the 1q, 2q, fidelities and parameters dataframes, with the last calibrations.

        Returns:
            dict[str, pd.DataFrame]: Last calibrations dataframes.
        """
        df_1q, df_2q = self.get_qubits_tables()

        return {
            "1q_table": df_1q,
            "2q_table": df_2q,
            "set_parameters": self.get_last_set_parameters(),
            "fidelities": self.get_last_fidelities(),
        }

    def run_fidelities(self) -> None:
        """Runs the fidelities notebooks."""
        fidelities_nodes = (node for node in self.node_sequence.values() if node.fidelity)
        for node in fidelities_nodes:
            self.calibrate(node)

    def maintain(
        self,
        node: CalibrationNode,
        force_mantain: bool = False,
        safe_diagnose: bool = False,
        strict_dependencies: bool = False,
    ) -> None:
        """Calls all the necessary subroutines (``check_state()``, ``check_data()`` and ``calibrate()``) in the respective dependencies to get a node
        in spec. Maintain contains the main workflow for our calibration procedure, and it's what is called from ``run_automatic_calibration()`` into
        each of the end ``nodes`` (leaves) of our graph.

        The algorithm starts from the `roots` that the passed ``node`` depends on, and moves forwards (`dependency -> dependant`) up to ``node``,
        at each step, first efficiently checking the last time executions (``check_state()``) until some fails, and then passes to check the data
        (``check_data()``, less efficient). If a problematic node is found, meaning, it doesn't pass ``check_state()`` and gives
        ``bad_data`` in ``check_data()``, then ``maintain()`` calls ``diagnose()`` for solving it.

        During all this process, the mid-level methods would be calling these low-level methods, that act on the nodes:
        ``calibrate()``, ``check_status()`` and ``check_data()``.

        Finally, ``maintain`` is designed to start acquiring data or calibrating in the optimal location of the graph, to avoid extra work:

        # TODO: Change this workflow explanations to new one
        - if node A has been calibrated very recently (before the ``drift_timeout`` of the :class:`.CalibrationNode`), it would be waste of resources to check its data, so ``check_state()`` makes ``maintain()`` skip it.
        - if node A depends on node B, before calibrating node A we check the data of node B, calibrating A would be a waste of resources if we were doing so based on faulty data, so it goes to its dependencies first.

        |

        # TODO: change this dangerous behaviours explanations, to new workflow
        Note that due to this, we can have dangerous behaviours in ``maintain()``, for example:

        - if you give bad ``comparison_thresholds`` or have bad ``comparison_models``, returning ``out_of_spec`` when you actually have ``bad_data`` or the other way around, making ``diagnose()`` not being able to work properly. Since for ``diagnose()`` to work, you need to have a single layer node separation (``out_of_spec``) between the ``in_spec`` and the ``bad_data`` nodes.
        - if you give too long ``drift_timeout``'s, since ``maintain()`` will assume the node is 100% working, you will go to further dependants, when maybe you shouldn't without recalibrating (in the end ``diagnose()`` saves the day here, since it doesn't do ``check_state()``, but in a less efficient way).

        .. note:: Find more information about the ``maintain()`` idea at https://arxiv.org/abs/1803.03226.

        Args:
            node (CalibrationNode): The node where we want to start the algorithm on, getting it in spec. Normally you would want
                this node to be the furthest node in the calibration graph.
            force_mantain (bool, optional): Flag to force the method to not considerate `check_status` output value,
                meaning it allways perform a call to `check_data`. Default to False.
            safe_diagnose (bool, optional): Flag to specify if we make sure to avoid corner cases while diagnosing (its slower). Defaults to False.
        """
        logger.info("WORKFLOW: Maintaining %s.\n", node.node_id)
        # Recursion over all the nodes that the current node depends on.
        for n in self._dependencies(node):
            self.maintain(n)

        # TODO: Integrationt test, where if all the drift_timeouts are super big, no check_data or calibration is done
        # TODO: when no force_maintain, and one in the end, when the flag exist.

        # If check_state of this node passes, don't check data, assume it works (unless its an end node).
        node_status = self.check_state(node, strict_dependencies=strict_dependencies)
        if not force_mantain and node_status:
            return

        # Check data, if bad, diagnose to find the problem.
        result = self.check_data(node)

        # If in_spec, maintain ends!
        if result == "in_spec":
            self._update_parameters(node)  # In case the runcard has changed from last calibration.
            return

        # TODO: Integration test, for the second condition here: for example, if we had check_data like
        # TODO: V - V - O - O then it would calibrate the last without calibrating the dependency...

        # If `bad_data` or `out_of_spec` in the last nodes with safe flag:
        if result == "bad_data" or (safe_diagnose and result == "out_of_spec"):
            for n in self._dependencies(node):
                logger.info("WORKFLOW: Diagnosing %s from maintain(%s).\n", n.node_id, node.node_id)
                self.diagnose(n, safe=safe_diagnose)

        # Implicit out_spec case (except above second condition with safe flag)
        if force_mantain and node_status:
            logger.info(
                "`force_maintain` in node %s, detected that `check_status` was passed, but node was not `in_spec', perhaps `drift_timeouts` should be updated.",
                node.node_id,
            )

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

        #TODO: Explain safe_check, this as example:
        Diagnose called with flag `safe_check` will make sure `out_spec` nodes are detected by reliying on actuall information of dependant nodes.
        Otherwise the algorithm will rely on `out_spec` classification method provided by the user via comparison model chosen.

        Note that `check` will cover corner cases that may be caused by user choices in exchange for time complexity as the number of
        calls to `check_data` will be higher on average.

        # TODO: change this dangerous behaviours explanations, to new workflow
        Finally mention, two important thing to have in mind:

        - if you give bad ``comparison_thresholds`` or have bad ``comparison_models``, which return ``out_of_spec`` when you actually have ``bad_data`` or the other way around, it will make your full calibration fail. Since for ``diagnose()`` to work, you need to have a single node separation (``out_of_spec``) between the ``in_spec`` and the ``bad_data`` ones.
        - if you have wrong ``drift_timeout``, the algorithm will be slower, but in the end ``diagnose()`` saves the day, achieving the full calibration, since it doesn't do ``check_state()``.

        .. note:: Find more information about the ``diagnose()`` idea at https://arxiv.org/abs/1803.03226.

        Args:
            node (CalibrationNode): The node where we want to start the algorithm.
            safe (bool, optional):  Flag to specify if we make sure to avoid corner cases (its slower). Defaults to False.

        Returns:
            bool: True is there have been recalibrations, False otherwise. The return value is only used by recursive calls.
        """
        logger.info("WORKFLOW: diagnosing %s.\n", node.node_id)

        if safe:
            # in spec case
            if self.check_data(node) == "in_spec":
                self._update_parameters(node)  # In case the runcard has changed from last calibration.
                return

            # bad_data/out_spec case
            for n in self._dependencies(node):
                self.diagnose(n, safe=True)

        else:
            result = self.check_data(node)

            # in spec case
            if result == "in_spec":
                self._update_parameters(node)  # In case the runcard has changed from last calibration.
                return False

            # bad data case
            recalibrated = []
            if result == "bad_data":
                recalibrated = [self.diagnose(n, safe=False) for n in self._dependencies(node)]
                logger.info("WORKFLOW: Dependencies diagnoses of %s: %s\n", node.node_id, str(recalibrated))
            # If not empty and only filled with False's (not any True).
            if recalibrated != [] and not any(recalibrated):
                return False

        # calibrate
        self.calibrate(node)
        self._update_parameters(node)
        return safe

    def check_state(self, node: CalibrationNode, strict_dependencies: bool = False) -> bool:
        """Checks if the node's drift timeouts have passed since the last calibration or data check.

        These timeouts represent how long it usually takes for the parameters to drift, specified by the user.

        Conditions for ``check_state()`` to pass:
            - The cal has had ``check_data()`` or ``calibrate()`` pass within the timeout period.
            - The cal has not failed ``calibrate()`` without resolution.
            - No dependencies have been recalibrated since the last time ``check_data()`` or ``calibrate()`` was run on this cal.
            - All dependencies pass ``check_state()``.

        .. note:: Find more information about the ``check_state()`` idea at https://arxiv.org/abs/1803.03226.

        Args:
            node (CalibrationNode): The node whose state needs to be checked.

        Returns:
            bool: True if the parameter's drift timeout has not yet expired, False otherwise.
        """
        # Check if something happened and the timestamp could not be setted properly
        if node.previous_timestamp is None:
            logger.info("WORKFLOW: check_state of %s: False.\n", node.node_id)
            return False

        # Get the list of the dependencies that have been calibrated before this node, all of them should be True
        for n in self._dependencies(node):
            # TODO: Integration test that cases where check_states are like: V - X - V - V only skip the first node
            # Keep the smaller drift timeout, from all its dependencies.
            if strict_dependencies and n.drift_timeout < node.drift_timeout:
                node.drift_timeout = n.drift_timeout
                logger.warning(
                    "The drift_timeout of node %s is bigger than its dependency %s, so the later will be used.",
                    node.node_id,
                    n.node_id,
                )
            # A dependency has been calibrated before this node
            if n.previous_timestamp >= node.previous_timestamp:
                logger.info("WORKFLOW: check_state of %s: False.\n", node.node_id)
                return False
            # A dependency is expired
            if self._is_timeout_expired(n.previous_timestamp, n.drift_timeout):
                logger.info("WORKFLOW: check_state of %s: False.\n", node.node_id)
                return False

        # If this node concretely passes check_state
        is_timeout_not_expired = not self._is_timeout_expired(node.previous_timestamp, node.drift_timeout)
        logger.info(
            "WORKFLOW: check_state of %s: %r.\n",
            node.node_id,
            is_timeout_not_expired,
        )
        return is_timeout_not_expired

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
        # 2 hour interval from last in_spec, for assuming is still good:
        if (node.previous_inspec is None or self._is_timeout_expired(node.previous_inspec, 7200.0)) and (
            node.previous_timestamp is None or self._is_timeout_expired(node.previous_timestamp, 7200.0)
        ):
            timestamp = node.run_node(check=True)
        else:
            logger.info('WORKFLOW: Using recent `in_spec`-`check_data` or calibration in node "%s".\n', node.node_id)
            return "in_spec"

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

            # TODO: Intergation test, that this returns the expected values, for very sided thresholds to
            # TODO: the right or to the left...

            comparison_number = self._obtain_comparison(node, obtain_params, compar_params)

            if comparison_number <= node.in_spec_threshold:
                comparison_result = "in_spec"
                node.previous_inspec = datetime.timestamp(datetime.now())

            elif comparison_number <= node.bad_data_threshold:
                comparison_result = "out_of_spec"

        # Do the necessary following changes:
        logger.info("WORKFLOW: check_data of %s: %s.\n", node.node_id, comparison_result)
        node._add_string_to_checked_nb_name(comparison_result, timestamp)  # add comparison result tag to the file name.
        node.output_parameters = node.previous_output_parameters
        return comparison_result

    def calibrate(self, node: CalibrationNode) -> None:
        """Runs a node's experiment on its default values of the ``sweep_interval``.

        This method is responsible for calibrating a node to bring it within spec. The calibration process is node-specific
        and depends on the notebook implementation and the calibration parameters.

        .. note:: Find more information about the ``calibrate()`` idea at https://arxiv.org/abs/1803.03226.

        Args:
            node (CalibrationNode): The node where the calibration experiment is run.
        """
        logger.info('WORKFLOW: Calibrating node "%s".\n', node.node_id)
        node.previous_timestamp = node.run_node()
        node.been_calibrated = True
        node._add_string_to_checked_nb_name("calibrated", node.previous_timestamp)  # pylint: disable=protected-access
        # add _calibrated tag to the file name, which doesn't have a tag.

    def _update_parameters(self, node: CalibrationNode) -> None:
        """Updates the node parameters value in the platform, after a calibration.

        If the node does not have an associated parameter, or the parameter attribute of the node is None,
        this function does nothing.

        Args:
            node (CalibrationNode): The node which parameters need to be updated in the platform.
        """
        if node.output_parameters is not None and "platform_parameters" in node.output_parameters:
            for bus_alias, param_name, param_value, channel_id in node.output_parameters["platform_parameters"]:
                logger.info(
                    "Platform updated with: (bus: %s, %s, %s, ch: %s).", bus_alias, param_name, param_value, channel_id
                )
                self.platform.set_parameter(
                    alias=bus_alias, parameter=ql.Parameter(param_name), value=param_value, channel_id=channel_id
                )

            save_platform(self.runcard, self.platform)

    def get_last_set_parameters(self) -> pd.DataFrame:
        """Retrieves the last set parameters of the graph.

        Returns:
            dict[tuple, tuple]: Set parameters dictionary, with the key and values being tuples containing, in this order:
                - ``key``: (``str``: parameter name, ``str``: bus alias, ``int``: qubit).
                - ``value``: (``float``: parameter value, ``str``: node_id where computed, ``datetime``: updated time).
        """
        parameters: dict[tuple, tuple] = {}
        for node in self.node_sequence.values():
            if (
                node.output_parameters is not None
                and node.previous_timestamp is not None
                and "platform_parameters" in node.output_parameters
            ):
                for bus_alias, param_name, param_value, channel_id in node.output_parameters["platform_parameters"]:
                    parameters[(param_name, bus_alias, channel_id)] = (
                        param_value,
                        node.node_id,
                        datetime.fromtimestamp(node.previous_timestamp),
                    )

        df = pd.DataFrame.from_dict(parameters).transpose()
        if len(df.columns) == 3:
            df.columns = ["value", "node_id", "datetime"]
        if df.index.nlevels == 3:
            df.index.names = ["parameter", "bus", "qubit"]
        return df

    def get_last_fidelities(self) -> pd.DataFrame:
        """Retrieves the last updated fidelities of the graph.

        Returns:
            dict[tuple, tuple]: Fidelities dictionary, with the key and values being tuples containing, in this order:
                - ``key``: (``str``: parameter name, ``int``: qubit).
                - ``value``: (``float``: parameter value, ``str``: node_id where computed, ``datetime``: updated time).
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

        df = pd.DataFrame.from_dict(fidelities).transpose()
        if len(df.columns) == 3:
            df.columns = ["fidelity", "node_id", "datetime"]
        if df.index.nlevels == 2:
            df.index.names = ["fidelity", "qubit"]
        return df

    def get_qubits_tables(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Retrieves the last updated fidelities of the graph in the 1 qubit and 2 qubit tables.

        Returns:
            tuple[pd.DataFrame]: Tables where columns are each fidelity or parameter, and rows each qubit.
        """
        q1_df, q2_df = self._create_empty_dataframes()

        for node in self.node_sequence.values():
            qubit_list = node.node_id.split("_")
            qubit = "_".join(
                [i for i in qubit_list if any(char == "q" for char in i) and any(char.isdigit() for char in i)]
            ).replace("q", "-")[1:]

            if len(qubit) == 1:
                q1_df = self._fill_qubits_columns(node, qubit, q1_df)

            else:
                q2_df = self._fill_qubits_columns(node, qubit, q2_df)

        # Reorder fidelities to the front of the dataframe:
        q1_df = self._reorder_fidelities(q1_df)
        q2_df = self._reorder_fidelities(q2_df)

        return q1_df, q2_df

    def _create_empty_dataframes(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Creates the structure of the dataframe for the qubits table.

        Returns:
            pd.DataFrame: Empty df, where columns are each fidelity or parameter, and rows each qubit.
        """
        q1_idx, q1_col, q2_idx, q2_col = [], [], [], []  # type: ignore[var-annotated]

        for node in self.node_sequence.values():
            qubit_list = node.node_id.split("_")
            qubit = "_".join(
                [i for i in qubit_list if any(char == "q" for char in i) and any(char.isdigit() for char in i)]
            ).replace("q", "-")[1:]

            if len(qubit) == 1:
                q1_idx, q1_col = self._get_idx_and_columns(node, qubit, q1_idx, q1_col)

            else:
                q2_idx, q2_col = self._get_idx_and_columns(node, qubit, q2_idx, q2_col)

        df_q1 = pd.DataFrame("-", q1_idx, q1_col)
        df_q1.index.name = "qubit"

        df_q2 = pd.DataFrame("-", q2_idx, q2_col)
        df_q2.index.name = "qubit"

        return df_q1, df_q2

    @staticmethod
    def _get_idx_and_columns(node: CalibrationNode, qubit: str, idx: list, col: list) -> tuple[list, list]:
        """Gets the index and columns for creating a dataframe for 1q or 2q.

        Args:
            node (CalibrationNode): Node for which we are currently creating the dataframe idx and columns.
            qubit (str): qubit for which we are currently creating the dataframe idx and columns, corresponding to the node.
            idx (list): idx to be added.
            col (list): column to be added.

        Returns:
            tuple[list, list]: list of idx and columns for creating the dataframe.
        """
        if qubit not in idx:
            idx.append(qubit)

        if node.output_parameters is not None and node.previous_timestamp is not None:
            if "fidelities" in node.output_parameters:
                for _, fidelity, _ in node.output_parameters["fidelities"]:
                    if fidelity not in col:
                        col.append(fidelity)

            if "platform_parameters" in node.output_parameters:
                for bus_alias, param_name, _, _ in node.output_parameters["platform_parameters"]:
                    bus_list = str(bus_alias).split("_")
                    bus = "_".join([x for x in bus_list if not any(char.isdigit() for char in x)])

                    if f"{str(param_name)}_{bus}" not in col:
                        col.append(f"{str(param_name)}_{bus}")

        return idx, col

    @staticmethod
    def _fill_qubits_columns(node: CalibrationNode, qubit: str, df: pd.DataFrame) -> pd.DataFrame:
        """Fills the qubit tables columns with the fidelities or parameters values.

        Args:
            node (CalibrationNode): Node currently being filled.
            qubit (str): qubit being filled, corresponding to the node.
            df (pd.DataFrame): Dataframe to fill.

        Returns:
            pd.DataFrame: Filled dataframe.
        """
        if node.output_parameters is not None and node.previous_timestamp is not None:
            if "fidelities" in node.output_parameters:
                for _, fidelity, value in node.output_parameters["fidelities"]:
                    df[fidelity][qubit] = value

            if "platform_parameters" in node.output_parameters:
                for bus_alias, param_name, param_value, _ in node.output_parameters["platform_parameters"]:
                    bus_list = str(bus_alias).split("_")
                    bus = "_".join([x for x in bus_list if not any(char.isdigit() for char in x)])
                    df[f"{str(param_name)}_{bus}"][qubit] = param_value

        return df

    @staticmethod
    def _reorder_fidelities(df: pd.DataFrame) -> pd.DataFrame:
        """It moves the fidelities columns to the front of the dataframe.

        Args:
            df (pd.DataFrame): Dataframe to reorder.

        Returns:
            pd.DataFrame: Reordered dataframe.
        """
        for column in df.columns:
            if "fidelity" in column:
                first_column = df.pop(column)
                df.insert(0, column, first_column)

        return df

    def _dependencies(self, node: CalibrationNode) -> list:
        """Finds the dependencies of a node.

        If in our graph we have `A -> B`, then node B depends on node A. Thus calling this method on B would return A.

        Args:
            node (CalibrationNode): The nodes for which the dependencies need to be retrieved.

        Returns:
            list: The nodes that the argument node depends on.
        """
        return [self.node_sequence[node_name] for node_name in self.calibration_graph.predecessors(node.node_id)]

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
        """Checks if the time passed since the ``timestamp`` is greater than the ``timeout`` duration.

        Args:
            timestamp (float): Timestamp from which the time should be checked, described in UNIX timestamp format.
            timeout (float): The timeout duration in seconds.

        Returns:
            bool: True if the ``timeout`` has expired, False otherwise.
        """
        # Calculate the time that should have passed (timestamp + timeout duration), convert them to datetime objects:
        timestamp_dt = datetime.fromtimestamp(timestamp)
        timeout_duration = timedelta(seconds=timeout)
        timeout_time = timestamp_dt + timeout_duration

        # Check if the current time is greater than the timeout time
        current_time = datetime.now()
        return current_time > timeout_time

    # TODO: @Isaac, I've commented this, because we won't use a ratio parameter, its too ugly and complex for a first iteration...
    # I would just delete this function, but if you really want, keep this one with a fixed number like 600, or a fixed small ratio like 0.01
    # Like it is now, its super beautiful and clear, two flags, nothing complicated, if hardware ask, we can always add it!

    # @staticmethod
    # def _get_forced_maintain_condition(node: CalibrationNode, ratio: float = 0.01) -> bool:
    #     """Method to return if a Calibration Node should be force maintained or not.
    #     The condition checks if the time transcurred from the last calibration is greater than a ratio of the drift timeout of the node.

    #     Args:
    #         node (CalibrationNode): Calibration Node to get the the forced maintain condition
    #         ratio(flat, optional): Ratio used for the condition. Default to 0.0.

    #     Returns:
    #         bool: Returns True if the condition is met. Otherwise returns False.
    #     """
    #     comp = node.drift_timeout * ratio if ratio != 0 else 600
    #     now = datetime.timestamp(datetime.now())
    #     return now - node.previous_timestamp > comp if node.previous_timestamp is not None else False
