import os

import lmfit
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import networkx as nx
import numpy as np
from scipy.signal import find_peaks

import qililab as ql
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


# Rabi experiment 
rabi_values = {"start": 0,
               "stop": 0.25,
               "step": (0.25-0)/40 # It's written like this because it's derived from a np.linspace definition
               }

sweep_interval_dummy = {"start": 0,
                        "stop": 10,
                        "step": 1
                        }

def rabi(drive_bus: str, readout_bus: str, sweep_values: dict):
    """The Rabi experiment written as a QProgram.

    Args:
        drive_bus (str): Name of the drive bus
        readout_bus (str): Name of the readout bus
        sweep_values (dict): The sweep values of the experiment. These are the values over which the loops of the qprogram iterate

    Returns:
        qp (QProgram): The QProgram describing the experiment. It will need to be compiled to be run on the qblox cluster.
    """
    qp = ql.QProgram()
    gain = qp.variable(float)

    # Adjust the arguments of DragPair based on the runcard
    drag_pair = DragPair(amplitude=1.0, duration=20, num_sigmas=4, drag_coefficient=0.0)

    ones_wf = Square(amplitude=1.0, duration=1000)
    zeros_wf = Square(amplitude=0.0, duration=1000)

    with qp.average(iterations=1000):
        # We iterate over the gain instead of amplitude because it's equivalent and we can't iterate over amplitude.
        with qp.for_loop(variable=gain, start = sweep_values["start"], stop = sweep_values["stop"], step = sweep_values["step"]):
            qp.set_gain(bus=drive_bus, gain_path0=gain, gain_path1=gain)
            qp.play(bus=drive_bus, waveform=drag_pair)
            qp.sync()
            qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
            qp.acquire(bus=readout_bus)

    return qp

def qprogram_dummy(drive_bus: str, readout_bus: str, sweep_values: dict):
    return ql.QProgram()

##################################### ANALYSIS ##################################################


def analyze_rabi(results, show_plot: bool, fit_quadrature="i", label=""):
    """
    Analyzes the Rabi experiment data.

    Args:
        results: Where the data experimental is stored. If it's a string, it represents the path of the yml file where the data is. 
                 Otherwise it's a list with only 1 element. This element is a dictionary containing the data.
                 For now this only supports experiment run on QBlox hardware. The dictionary is a standard structure in which the data 
                 is stored by the QBlox hardware. For more details see this documentation: 
                 https://qblox-qblox-instruments.readthedocs-hosted.com/en/master/api_reference/pulsar.html#qblox_instruments.native.Pulsar.get_acquisitions
                 The list only has 1 element because each element represents the acquisitions dictionary of one readout bus, 
                 and for the moment multiple readout buses are not supported.
        show_plot (bool): If true, the plot is saved and printed so the user can see it. If false, the plot is just saved.

    Returns:
        fitted_pi_pulse_amplitude (int)
    """

    # Get the path of the experimental data file
    if isinstance(results, str):
        # The 'results' argument is the path to the file where the results are stored.
        parent_directory = os.path.dirname(results)
        figure_filepath = os.path.join(parent_directory, "Rabi.PNG")
        data_raw = get_raw_data(results)
    elif isinstance(results, list):
        # The 'results' argument is list where the elements are dictionaries storing the raw results.
        # FIXME: This implementation will have to change when multiple readout buses are supported, because then the results list 
        # will contain more than one element. See the 'run' method src/qililab/execution/execution_manager.py for more details.
        data_raw = results[0]
    

    amplitude_loop_values = np.array(data_raw["loops"][0]["values"])
    swept_variable = data_raw["loops"][0]["parameter"]
    this_shape = len(amplitude_loop_values)

    # Get flattened data and shape it
    i, q = get_iq_from_raw(data_raw)
    i = i.reshape(this_shape)
    q = q.reshape(this_shape)

    fit_signal = i if fit_quadrature == "i" else q
    fit_signal_idx = 0 if fit_quadrature == "i" else 1

    # Fit
    def sinus(x, a, b, c, d):
        return a * np.sin(2 * np.pi * b * np.array(x) - c) + d

    # TODO: hint values are pretty random, they should be tuned better. Trial and error seems to be the best way.
    mod = lmfit.Model(sinus)
    mod.set_param_hint("a", value=1 / 2, vary=True, min=0)
    mod.set_param_hint("b", value=0, vary=True)
    mod.set_param_hint("c", value=0, vary=True)
    mod.set_param_hint("d", value=1 / 2, vary=True, min=0)

    params = mod.make_params()
    fit = mod.fit(data=fit_signal, params=params, x=amplitude_loop_values)

    a_value = fit.params["a"].value
    b_value = fit.params["b"].value
    c_value = fit.params["c"].value
    d_value = fit.params["d"].value

    optimal_parameters = [a_value, b_value, c_value, d_value]
    fitted_pi_pulse_amplitude = np.abs(1 / (2 * optimal_parameters[1]))

    # Plot
    title_label = f"{label}"
    fig, axes = plot_iq(amplitude_loop_values, i, q, title_label, swept_variable)
    plot_fit(
        amplitude_loop_values, optimal_parameters, axes[fit_signal_idx], fitted_pi_pulse_amplitude
    )
    fig.savefig(figure_filepath, format="PNG")
    if show_plot:
        plot = mpimg.imread(figure_filepath)
        plt.imshow(plot)
        plt.show(block=False)
    return fitted_pi_pulse_amplitude

def analysis_dummy(results, show_plot: bool):
    optimal_parameter_value_dummy = 1.0
    return optimal_parameter_value_dummy


##################################### GRAPH ##########################################################

# TODO:
# * I don't know if, with the new buses, we need both the parameter and alias arguments.
# * The name given to alias here is not ok: the parameter update fails because the platform can't find an instrument with that alias: what's a good alias for this experiment?
rabi_1_node = CalibrationNode(
    node_id="rabi_1",
    qprogram=rabi,
    sweep_interval=rabi_values,
    analysis_function=analyze_rabi,
    qubit=0,
    parameter=ql.Parameter.AMPLITUDE,
    alias="drive_line_q0_bus",
    manual_check=False
)

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
    
######################################################################################################
"""
Initialize the controller and start the calibration algorithm.
"""
controller = Controller(calibration_sequence_name= 'test_sequence', platform = platform, calibration_graph = calibration_graph, manual_check_all=True)

# Start automatic calibration
controller.run_calibration()