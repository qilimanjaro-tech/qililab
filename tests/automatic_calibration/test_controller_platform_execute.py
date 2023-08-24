import os

import lmfit
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import networkx as nx
import numpy as np

import qililab as ql
from qililab.platform import Platform
from qililab.automatic_calibration import CalibrationNode, Controller
from qililab.automatic_calibration.calibration_utils.calibration_utils import get_raw_data, get_iq_from_raw, plot_iq, plot_fit, get_timestamp

from qibo.models import Circuit
from qibo import gates
from qililab.pulse.circuit_to_pulses import CircuitToPulses

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

def rabi(drive_bus: str, readout_bus: str, sweep_values: dict, platform: Platform):
    """
    TODO: rewrite for pulse schedule experiment.
    The Rabi experiment written as a QProgram.

    Args:
        drive_bus (str): Name of the drive bus
        readout_bus (str): Name of the readout bus
        sweep_values (dict): The sweep values of the experiment. These are the values over which the loops of the qprogram iterate

    Returns:
        qp (QProgram): The QProgram describing the experiment. It will need to be compiled to be run on the qblox cluster.
    """
        
    circuit = Circuit(1)
    circuit.add(gates.X(0))
    circuit.add(gates.M(0))

    pulse_schedule = CircuitToPulses(platform=platform).translate(circuits=[circuit])

    results = []
    gain_values = np.arange(sweep_values["start"], sweep_values["stop"], sweep_values["step"])
    for gain in gain_values:
        platform.set_parameter(alias=drive_bus, parameter=ql.Parameter.GAIN, value=gain)
        result = platform.execute(program=pulse_schedule, num_avg=1000, repetition_duration=6000)
        results.append(result.array)
    results = np.hstack(results)
##################################### ANALYSIS ##################################################


def analyze_rabi(results: str | dict, fit_quadrature="i", label=""):
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
                 
    Returns:
        fitted_pi_pulse_amplitude (int)
    """

    # Get the path of the experimental data file
    if isinstance(results, str):
        # The 'results' argument is the path to the file where the results are stored. 
        # NOTE: this is only here to maintain backwards compatibility. Remove asap.
        parent_directory = os.path.dirname(results)
        figure_filepath = os.path.join(parent_directory, "Rabi.PNG")
        data_raw = get_raw_data(results)
    elif isinstance(results, dict):
        # The 'results' argument is a dictionary storing the raw results.
        # FIXME: This implementation will have to change when multiple readout buses are supported, because then 'results' 
        # will be a list with more than one element, where each element is the results of a specific readout bus. 
        # See the 'run' method src/qililab/execution/execution_manager.py for more details.
        data_raw = results
        figure_filepath = "./tests/automatic_calibration/Rabi.PNG"
    else: 
        raise ValueError("Results are in incompatible format. They should be either a string representing a filepath or a dictionary")

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
    #TODO: save the plot here, not in Controller class.
    return fitted_pi_pulse_amplitude, fig, figure_filepath


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
    drift_timeout=1,
    manual_check=True
)

# Uncomment the following line to test check_state
#rabi_1_node.add_timestamp(timestamp=get_timestamp(), type_of_timestamp="calibration")

calibration_graph = nx.DiGraph()

nodes = [    
    rabi_1_node
]

calibration_graph.add_nodes_from(nodes)

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
controller = Controller(calibration_sequence_name= 'test_sequence_1_node', platform = platform, calibration_graph = calibration_graph, manual_check_all=False)

# Start automatic calibration
controller.run_calibration()