import argparse

import networkx as nx
import yaml
from controller import Controller

from qililab.automatic_calibration.experiment import Experiment


def build_graph_from_yaml(file_path):
    """Given a YAML file describing a directed acyclic graph, build the graph.
    Args:
        file_path (str): path of the YAML file describing a directed acyclic graph.

    Returns:
        nx.DiGraph: The directed acyclic graph specified by the YAML
    """
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    G = nx.DiGraph()

    for node_id, node_data in data.items():
        node = Experiment(node_id, node_data["attribute1"], node_data["attribute2"])
        G.add_node(node)

        for connection in node_data["connections"]:
            G.add_edge(node_id, connection)

    return G


def parse_args():
    """Asks the user to input some arguments and parses them.

    Returns:
       dict: The parsed arguments.
    """

    # TODO: Ask the user if they want to create graph or load existing one.
    parser = argparse.ArgumentParser(description="Build a DAG and store in YAML file.")
    parser.add_argument(
        "--yaml-file", type=str, required=True, help="Path to the YAML file for storing the graph data."
    )
    # Add other arguments for node attributes and connections as needed

    return parser.parse_args()


def get_user_input():
    """Using the  user input, build a graph and store it in a YAML file.

    Returns:
        nx.DiGraph: The graph specified by the user.
    """
    args = parse_args()

    user_data = {
        "node1": {
            "attribute1": args["attribute1"],
            "attribute2": args["attribute2"],
            "connections": args["connections"],
        },
        # Add other nodes and their data
    }

    with open(args["yaml_file_path"], "w") as f:
        yaml.dump(user_data, f)

    return build_graph_from_yaml(args["yaml_file_path"])


calibration_graph = get_user_input()
controller = Controller(calibration_graph)

# And let the magic begin...
controller.run_calibration()
