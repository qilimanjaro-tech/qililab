import os

import networkx as nx

from qililab.automatic_calibration import CalibrationController, CalibrationNode, norm_root_mean_sqrt_error

# Change relative os path
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Get galadriel runcard (WHICH NEEDS TO BE CHANGED)
path_runcard = abspath.split("qililab")[0] + "qililab/examples/runcards/galadriel.yml"

personalized_sweep_interval = {
    "start": 10,
    "stop": 50,
    "step": 2,
}

# CREATE NODES :
# (currently comparison return 3 for all notebooks, and when we calibrate we set the thresholds to 10)
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
third = CalibrationNode(
    nb_path="notebooks/third.ipynb",
    in_spec_threshold=1,
    bad_data_threshold=2,
    comparison_model=norm_root_mean_sqrt_error,
    drift_timeout=1.0,
    sweep_interval=personalized_sweep_interval,
    number_of_random_datapoints=5,
)

# NODE MAPPING TO THE GRAPH (key = name in graph, value = node object):
nodes = {"first": first, "second": second, "third": third}

# GRAPH CREATION:
G = nx.DiGraph()
G.add_edge("third", "second")
G.add_edge("second", "first")

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
