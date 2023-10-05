import os

import networkx as nx

from qililab.automatic_calibration import CalibrationController, CalibrationNode

# Change relative os path
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

# Get galadriel runcard (WHICH NEEDS TO BE CHANGED)
path_runcard = abspath.split("qililab")[0] + "qililab/examples/runcards/galadriel.yml"

# CREATE NODES:
first = CalibrationNode(nb_path="notebooks/first.ipynb", in_spec_threshold=0.1, bad_data_threshold=0.2, drift_timeout=1800.0)
second = CalibrationNode(nb_path="notebooks/second.ipynb", in_spec_threshold=0.1, bad_data_threshold=0.2, drift_timeout=1.0)
third = CalibrationNode(nb_path="notebooks/third.ipynb", in_spec_threshold=0.1, bad_data_threshold=0.2, drift_timeout=1.0)

# NODE MAPPING TO THE GRAPH (key = name in graph, value = node object):
nodes = {"first": first, "second": second, "third": third}

# GRAPH CREATION:
G = nx.DiGraph()
G.add_edge("third", "second")
G.add_edge("second", "first")

# CREATE CALIBRATION CONTROLLER:
controller = CalibrationController(node_sequence=nodes, calibration_graph=G, runcard=path_runcard)


### EXTRA THINGS, WHICH WILL NOT BE NEEDED IN THE FUTURE:
first.output_parameters = {"check_parameters": {
        "x": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
        "y": [2, 1, 3, 42, 5, 6, 7, 8, 9, 10, 11, 12, 13, 114, 15, 16, 17, 18, 19]
}}
second.output_parameters = {"check_parameters": {
    "x": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
    "y": [2, 1, 3, 14, 5, 6, 7, 8, 9, 10, 111, 12, 13, 14, 15, 168, 17, 18, 19],
}}
third.output_parameters = {"check_parameters": {
        "x": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
        "y": [2, 1, 3, 4, 15, 6, 7, 8, 9, 10, 11, 12, 13, 4, 15, 16, 17, 18, 19],
}}


### EXECUTIONS TO DO:

# Calibrate the nodes, for when we have fucked up:
# controller.calibrate(first)
# controller.calibrate(second)
# controller.calibrate(third)

# Maintain from highest node:
controller.maintain(third)
