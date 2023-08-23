import os

import lmfit
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import networkx as nx
import numpy as np

import qililab as ql
from qililab.settings import Runcard
from qililab.automatic_calibration import CalibrationNode, Controller
from qililab.automatic_calibration.calibration_utils.calibration_utils import get_raw_data, get_iq_from_raw, plot_iq, plot_fit
from qililab.waveforms import DragPair, IQPair, Square

##################################### PLATFORM ####################################################
""" Define the platform and connect to the instruments """

os.environ["RUNCARDS"] = "./tests/automatic_calibration/runcards"
os.environ["DATA"] = "./tests/automatic_calibration/data"
platform_name = "galadriel"
platform = ql.build_platform(name=platform_name)

# Uncomment the following when working with an actual platform
#platform.connect()
#platform.turn_on_instruments()
#platform.initial_setup()

##################################### EXPERIMENTS ##################################################

sweep_interval_dummy = {"start": 0,
                        "stop": 10,
                        "step": 1
                        }

def qprogram_dummy(drive_bus: str, readout_bus: str, sweep_values: dict):
    return ql.QProgram()

##################################### ANALYSIS ##################################################
    
def analysis_dummy(results):
    optimal_parameter_value_dummy = 1.0
    fig = plt.figure()
    figure_filepath = "tests/automatic_calibration/drag.PNG"
    return optimal_parameter_value_dummy, fig, figure_filepath


##################################### GRAPH ##########################################################

# TODO:
# * I don't know if, with the new buses, we need both the parameter and alias arguments.
# * The name given to alias here is not ok: the parameter update fails because the platform can't find an instrument with that alias: what's a good alias for this experiment?

dummy_1_node = CalibrationNode(
    node_id="dummy_1",
    qprogram=qprogram_dummy,
    sweep_interval=sweep_interval_dummy,
    is_refinement=False,
    analysis_function=analysis_dummy,
    fitting_model=None,
    plotting_labels=None,
    qubit=0,
    parameter=None,
    alias=None,
    drift_timeout=0,
    data_validation_threshold=1,
    number_of_random_datapoints=1,
    manual_check=False
)
dummy_2_node = CalibrationNode(
    node_id="dummy_2",
    qprogram=qprogram_dummy,
    sweep_interval=sweep_interval_dummy,
    is_refinement=False,
    analysis_function=analysis_dummy,
    fitting_model=None,
    plotting_labels=None,
    qubit=0,
    parameter=None,
    alias=None,
    drift_timeout=0,
    data_validation_threshold=1,
    number_of_random_datapoints=1,
    manual_check=False
)

calibration_graph = nx.DiGraph()

nodes = [    
    dummy_1_node, 
    dummy_2_node
]

calibration_graph.add_nodes_from(nodes)

calibration_graph.add_edge(dummy_2_node, dummy_1_node)

# Visualization of the calibration graph
labels = {node: node.node_id for node in calibration_graph.nodes}
nx.draw_planar(calibration_graph, labels=labels, with_labels=True)
graph_figure_filepath ="./tests/automatic_calibration/calibration_graph.PNG"
plt.savefig(graph_figure_filepath, format="PNG")

show_calibration_graph = False

if show_calibration_graph:
    graph_figure = mpimg.imread(graph_figure_filepath)
    plt.imshow(graph_figure)
    plt.show()
    
# This closes the figure containing the graph drawing. Every time we call plt.show() in the future, 
# for example to show the plot given by an analysis function to the user, all open figures will be shown,
# including this one showing the graph drawing, which we don't want.
plt.close()     
######################################################################################################
"""
Initialize the controller and start the calibration algorithm.
"""
controller = Controller(calibration_sequence_name= 'test_sequence', platform = platform, calibration_graph = calibration_graph, manual_check_all=True)

# Start automatic calibration
controller.run_calibration()