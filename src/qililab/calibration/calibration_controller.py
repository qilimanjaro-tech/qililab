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
from typing import TYPE_CHECKING

import networkx as nx
import pandas as pd

from qililab import Parameter
from qililab.calibration.calibration_node import CalibrationNode
from qililab.config import logger
from qililab.data_management import build_platform, save_platform

if TYPE_CHECKING:
    from qililab.platform.platform import Platform


class CalibrationController:
    """Controls the automatic calibration sequence.

    **Usage:**
        - To calibrate the full graph, use the ``run_automatic_calibration()`` method.

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
        #                    \\     v     /
        #                     \\--> 1 -->/

    .. note::

        Find information about the automatic-calibration workflow, in the examples below.

    Args:
        calibration_graph (nx.DiGraph): The calibration (directed acyclic) graph, where each node is a ``string`` corresponding to a ``CalibrationNode.node_id``. Directions should be given
            by `nodes` pointing to their next `dependents` (natural time flow for calibration), defining our `starts` and `ends` of the calibration as the `roots` (``in_degree=0``) and `leaves`
            (``out_degree=0``) of the graph.
        node_sequence (dict[str, CalibrationNode]): Mapping for the nodes of the graph, from strings into the actual initialized nodes.
        runcard (str): The runcard path, containing the serialized platform where the experiments will be run.
        drift_timeout (float, optional): Duration in seconds, representing an estimate of how long it takes for the calibration parameters to drift.
            During that time the parameters of this node should be considered calibrated. Thus a big value will tend to skip recently calibrated nodes,
            making the calibration process faster, but less accurate,and a small value will make the calibration process slower, but more accurate and robust.
            A node will be skipped if the ``drift timeout`` is bigger than the time since its last calibration. Defaults to 7200 (3h).

    |

    **Calibration Workflow:**

    The calibration process is structured into three levels of methods:

    1. **Highest Level Method**: The ``run_automatic_calibration()`` method finds all the end nodes of the graph (`leaves`, those without further `dependents`) and runs ``calibrate_all()`` on them.

    2. **Mid-Level Method**: ``calibrate_all()``.
        - ``calibrate_all(node)`` starts from the `roots` that ``node`` depends on, and moves forwards (`dependency -> dependant`) until ``node``, checking the last time executions at each step.

    3. **Low-Level Method**: ``calibrate()`` is the method you would be calling during this process to interact with the ``nodes``.


    ----------

    **Dangerous Behaviors:**

    Note that depending on your ``CalibrationController`` construction, you can have dangerous behaviors in the workflow. You need to watch out for:
    - If you give too long ``drift_timeout``'s, since ``calibrate_all()`` will assume the node is 100% working.. To start the calibration from the start again, just reduce the ``drift_timeout``, or remove the executed files!

    ----------

    Examples:

        To calibrate four different qubits, each with two sequential 1Q experiments (nodes: first and second), and two 2Q gate experiments connecting qubits 0-1 and 2-3 (nodes: joint_first and joint_second):

        .. code-block:: python

            # qubit_0: first -> second \\
            #                           -> joint_first[0,1] -> joint_second[0,1]
            # qubit_1: first -> second /
            #
            #
            # qubit_2: first -> second \\
            #                           -> joint_first[2,3] -> joint_second[2,3]
            # qubit_3: first -> second /

        you first need to create the 1Q nodes (and import the needed packages):

        .. code-block:: python

            import numpy as np
            import networkx as nx

            from qililab.calibration import CalibrationController, CalibrationNode, norm_root_mean_sqrt_error

            # GRAPH CREATION AND NODE MAPPING (key = name in graph, value = node object):
            nodes = {}
            G = nx.DiGraph()
            last_layer_1qb_nodes = []

            # CREATE NODES:
            for qubit in [0, 1, 2, 3]:
                first = CalibrationNode(
                    nb_path="notebooks/first.ipynb",
                    qubit_index=qubit,
                )
                nodes[first.node_id] = first

                second = CalibrationNode(
                    nb_path="notebooks/second.ipynb",
                    qubit_index=qubit,
                    sweep_interval=np.arange(start=0, stop=19, step=1),
                )
                nodes[second.node_id] = second

                # STORE LAST NODE OF EACH QUBIT, TO CONNECT THEM LATER TO A 2Q NODE:
                last_layer_1qb_nodes.append(second.node_id)

                # GRAPH BUILDING (1st --> 2nd):
                G.add_edge(first.node_id, second.node_id)

        Then you can add the 2Q nodes, explicitly writing its dependence, which would calibrate sequentially each of the two separate
        graphs (qubits 0 and 1 + joint[0,1] first, and qubits 2 and 3 + joint[2,3] later):

        .. code-block:: python

            # ADD 2Q NODES DEPENDING ON THE 1Q NODES:
            for qubits in [[0, 1], [2, 3]]:
                joint_first = CalibrationNode(
                    nb_path="notebooks/joint_first.ipynb",
                    qubit_index=qubits,
                    sweep_interval=np.arange(start=0, stop=19, step=1),
                )
                nodes[joint_first.node_id] = joint_first

                joint_second = CalibrationNode(
                    nb_path="notebooks/joint_second.ipynb",
                    qubit_index=qubits,
                    sweep_interval=np.arange(start=0, stop=19, step=1),
                )
                nodes[joint_second.node_id] = joint_second

                # GRAPH BUILDING (second 1Q Nodes -> first 2Q (joint) Nodes):
                G.add_edge(last_layer_1qb_nodes[qubits[0]], joint_first.node_id)
                G.add_edge(last_layer_1qb_nodes[qubits[1]], joint_first.node_id)

                # GRAPH BUILDING (joint_1st --> joint_2nd):
                G.add_edge(joint_first.node_id, joint_second.node_id)


        Or in reality you can skip the explicit connection of the 1Q gates to the 2Q gates, and just pass them as a separate graph
        posteriorly, calibrating all the 1Q gates first, and then all the 2Q gates:

        .. code-block:: python

            # ADD 2Q NODES DEPENDING ON THE 1Q NODES:
            for qubits in [[0, 1], [2, 3]]:
                joint_first = CalibrationNode(
                    nb_path="notebooks/joint_first.ipynb",
                    qubit_index=qubits,
                    sweep_interval=np.arange(start=0, stop=19, step=1),
                )
                nodes[joint_first.node_id] = joint_first

                joint_second = CalibrationNode(
                    nb_path="notebooks/joint_second.ipynb",
                    qubit_index=qubits,
                    sweep_interval=np.arange(start=0, stop=19, step=1),
                )
                nodes[joint_second.node_id] = joint_second

                # GRAPH BUILDING (joints_1st --> joints_2nd):
                G.add_edge(joint_first.node_id, joint_second.node_id) # If you only have one, you can just add_node(...).

        To finally create the ``CalibrationController`` and run the automatic calibration:

        .. code-block:: python

            # CREATE CALIBRATION CONTROLLER:
            controller = CalibrationController(node_sequence=nodes, calibration_graph=G, runcard=path_runcard)

            ### MAIN WORKFLOW TO DO:
            controller.run_automatic_calibration() # calibrate all the nodes in the graph, starting from the root until the leaves.

        .. note::

            Find information about how these nodes and their notebooks need to be in the :class:`CalibrationNode` class documentation.

    """

    def __init__(
        self,
        calibration_graph: nx.DiGraph,
        node_sequence: dict[str, CalibrationNode],
        runcard: str,
        drift_timeout: float = 7200.0,
    ):
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
            #                    \\     v     /
            #                     \\--> 1 -->/
        """

        self.node_sequence: dict[str, CalibrationNode] = node_sequence
        """Mapping for the nodes of the graph, from strings into the actual initialized nodes (dict)."""

        self.runcard: str = runcard
        """The runcard path, containing the serialized platform where the experiments will be run (str)."""

        self.platform: Platform = build_platform(runcard)
        """The initialized platform, where the experiments will be run (Platform)."""

        self.drift_timeout: float = drift_timeout
        """Duration in seconds, representing an estimate of how long it takes for the calibration parameters to drift.
        During that time the parameters of this node should be considered calibrated.

        Thus a big value will tend to skip recently calibrated nodes, making the calibration process faster, but less accurate,
        and a small value will make the calibration process slower, but more accurate and robust.

        A node will be skipped if the ``drift timeout`` is bigger than the time since its last calibration. Defaults to 7200 (2h).
        """

    def run_automatic_calibration(self) -> dict[str, dict]:
        """Runs the full automatic calibration procedure and retrieves the final set parameters and achieved fidelities dictionaries.

        This is the primary interface for our calibration procedure and the highest level algorithm, which finds all the end nodes of the graph
        (`leaves`, those without further `dependents`) and runs ``calibrate_all()`` on them.

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
            self.node_sequence[node] for node, out_degree in self.calibration_graph.out_degree() if out_degree == 0
        ]

        for node in highest_level_nodes:
            self.calibrate_all(node)

        logger.info(
            "\n#############################################\n"
            "Automatic calibration completed successfully!\n"
            "#############################################\n"
        )
        return self.get_qubit_fidelities_and_parameters_df_tables()

    def calibrate_all(self, node: CalibrationNode):
        """Given a node to start from, calibrates all the dependency notebooks sequentially, so that the given node can be calibrated last.

        Args:
            node (CalibrationNode): The node where we want to start the `calibration_all()` on. Normally you would want
                this node to be the furthest node in the calibration graph.
        """
        logger.info("WORKFLOW: Calibrating all %s.\n", node.node_id)
        for n in self._dependencies(node):
            self.calibrate_all(n)

        # You can skip it from the `drift_timeout`, but also skip it due to `been_calibrated()`
        # If you want to start the calibration from the start again, just decrease the `drift_timeout` or remove the executed files!
        if not node.been_calibrated:
            if node.previous_timestamp is None or self._is_timeout_expired(node.previous_timestamp, self.drift_timeout):
                self.calibrate(node)
                self._update_parameters(node)

            node.been_calibrated = True
        # After passing this block `node.been_calibrated` will always be True, so it will not be recalibrated again.

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
        node._add_string_to_checked_nb_name("calibrated", node.previous_timestamp)
        # add _calibrated tag to the file name, which doesn't have a tag.

    def _update_parameters(self, node: CalibrationNode) -> None:
        """Updates the node parameters value in the platform, after a calibration.

        If the node does not have an associated parameter, or the parameter attribute of the node is None,
        this function does nothing.

        The `node.output_parameters["platform_parameters"]` needs to be a list with the same order as in
        `platform.set_parameter()`:
            - `param_name`: The name of the parameter to be updated.
            - `param_value`: The value of the parameter to be updated.
            - `bus_alias`: The bus alias where the parameter is located.
            - `channel_id`: The channel id where the parameter is located.

        Args:
            node (CalibrationNode): The node which parameters need to be updated in the platform.
        """
        if node.output_parameters is not None and "platform_parameters" in node.output_parameters:
            for param_name, param_value, bus_alias, channel_id in node.output_parameters["platform_parameters"]:
                logger.info(
                    "Platform updated with: %s, %s, (bus: %s, ch: %s).", param_name, param_value, bus_alias, channel_id
                )
                self.platform.set_parameter(
                    parameter=Parameter(param_name), value=param_value, alias=bus_alias, channel_id=channel_id
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
                for param_name, param_value, bus_alias, channel_id in node.output_parameters["platform_parameters"]:
                    parameters[param_name, bus_alias, channel_id] = (
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
                    fidelities[fidelity, qubit] = (
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
            qubit = self._get_qubit_from_node(node)
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
            qubit = self._get_qubit_from_node(node)
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
    def _get_qubit_from_node(node) -> str:
        """Retrieves the qubit from the node_id.

        Args:
            node (CalibrationNode): The node from which the qubit needs to be retrieved.

        Returns:
            str: The qubit corresponding to the node.
        """
        qubits: list = node.node_id.split("_")
        return "_".join(
            [i for i in qubits if any(char == "q" for char in i) and any(char.isdigit() for char in i)]
        ).replace("q", "-")[1:]

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
                for param_name, _, bus_alias, _ in node.output_parameters["platform_parameters"]:
                    bus = CalibrationController._get_bus_name_from_alias(bus_alias)
                    if f"{param_name!s}_{bus}" not in col:
                        col.append(f"{param_name!s}_{bus}")

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
                for param_name, param_value, bus_alias, _ in node.output_parameters["platform_parameters"]:
                    bus = CalibrationController._get_bus_name_from_alias(bus_alias)
                    df[f"{param_name!s}_{bus}"][qubit] = param_value

        return df

    @staticmethod
    def _get_bus_name_from_alias(bus_alias) -> str:
        """Gets the bus name from the bus alias.

        Args:
            bus_alias (str): Bus alias to get the bus name from.

        Returns:
            str: The bus name.
        """
        buses: list = str(bus_alias).split("_")
        return "_".join([x for x in buses if not any(char.isdigit() for char in x)])

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
