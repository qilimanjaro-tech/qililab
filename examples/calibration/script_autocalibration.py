import os

import networkx as nx
import numpy as np

from qililab.calibration import CalibrationController, CalibrationNode, norm_root_mean_sqrt_error

# Change relative os path
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Get galadriel runcard (WHICH NEEDS TO BE CHANGED)
path_runcard = abspath.split("qililab")[0] + "qililab/examples/runcards/galadriel.yml"

personalized_sweep_interval = np.arange(10, 50, 2)

# NODE MAPPING TO THE GRAPH (key = name in graph, value = node object):
nodes = {}
G = nx.DiGraph()

# CREATE NODES :
# (currently comparison return 3 for all notebooks, and when we calibrate we set the thresholds to 10)
for qubit in [0, 1, 2, 3, 4]:
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
        sweep_interval=personalized_sweep_interval,
    )
    nodes[second.node_id] = second

    third = CalibrationNode(
        nb_path="notebooks/third.ipynb",
        qubit_index=qubit,
        in_spec_threshold=1,
        bad_data_threshold=2,
        comparison_model=norm_root_mean_sqrt_error,
        drift_timeout=1.0,
        sweep_interval=personalized_sweep_interval,
        number_of_random_datapoints=5,
    )
    nodes[third.node_id] = third

    # GRAPH CREATION:
    G.add_edge(first.node_id, second.node_id)
    G.add_edge(second.node_id, third.node_id)

nx.draw(G)

# CREATE CALIBRATION CONTROLLER:
controller = CalibrationController(node_sequence=nodes, calibration_graph=G, runcard=path_runcard)


### EXECUTIONS TO DO:

# Create the first notebook executions, for when we have fucked up:
controller.calibrate(first)
first.in_spec_threshold, first.bad_data_threshold = 4, 8
controller.calibrate(second)
second.in_spec_threshold, second.bad_data_threshold = 2, 4
controller.calibrate(third)
third.in_spec_threshold, third.bad_data_threshold = 1, 2

# Maintain from highest node:
# controller.maintain(third)
