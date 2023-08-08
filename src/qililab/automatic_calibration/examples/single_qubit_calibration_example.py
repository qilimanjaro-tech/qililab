import json
import os

import networkx as nx
import numpy as np
import lmfit
import matplotlib.pyplot as plt

import qililab as ql
from qililab import qprogram
import qililab.automatic_calibration.calibration_utils.calibration_utils as calibration_utils
from qililab.automatic_calibration.calibration_node import CalibrationNode
from qililab.automatic_calibration.controller import Controller
from qililab.platform.platform import Platform
from qililab.waveforms import DragPulse, IQPair, Square

# Create the nodes for a calibration graph

#################################################################################################
""" Define the platform and connect to the instruments"""

os.environ["RUNCARDS"] = "../runcards"
os.environ["DATA"] = f"../data"
platform_name = "soprano_master_galadriel"
platform = ql.build_platform(name=platform_name)
platform.filepath = os.path.join(
    os.environ["RUNCARDS"], f"{platform_name}.yml"
)

platform.connect()
platform.turn_on_instruments()
platform.initial_setup()

######################################################################################################
""" Define the QPrograms, i.e. the experiments that will be the nodes of the calibration graph """


# Rabi experiment node
rabi_values = np.linspace(0, 0.25, 41)
fine_rabi_values = np.arange(-0.1, 0.1, 0.001)


def rabi(drive_bus: str, readout_bus: str, sweep_values: list[int]):
    """The rabi experiment written as a QProgram.

    Args:
        drive_bus (str): Name of the drive bus
        readout_bus (str): Name of the readout bus

    Returns:
        QProgram: The QProgram describing the experiment. It will need to be compiled to be run on the qblox cluster.
    """
    qp = ql.QProgram()
    gain = qp.variable(float)

    # Adjust the arguments of DragPulse based on the runcard
    drag_pair = DragPulse(amplitude=1.0, duration=20, num_sigmas=4, drag_coefficient=0.0)
    
    ones_wf = Square(amplitude=1.0, duration=1000)
    zeros_wf = Square(amplitude=0.0, duration=1000)

    with qp.acquire_loop(iterations=1000):
        # We iterate over the gain instead of amplitude because it's equivalent and we can't iterate over amplitude.
        with qp.loop(variable=gain, values=sweep_values):
            qp.set_gain(bus=drive_bus, gain_path0=gain, gain_path1=gain)
            qp.play(bus=drive_bus, waveform=drag_pair)
            qp.sync()
            qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
            qp.acquire(bus=readout_bus)

    return qp


# Ramsey experiment node (it's run twice to refine values)
# TODO: implement this once parallel loops are supported by qprogram
wait_values = np.arange(8.0, 1000, 20)
fine_if_values = np.arange(-2e6, 2e6, 0.2e6)


def ramsey(drive_bus: str, readout_bus: str):
    qp = ql.QProgram()
    wait_time = qp.variable(int)

    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    ones_wf = Square(amplitude=1.0, duration=1000)
    zeros_wf = Square(amplitude=0.0, duration=1000)

    with qp.acquire_loop(iterations=1000):
        with qp.loop(variable=wait_time, values=wait_values):
            qp.play(bus=drive_bus, waveform=drag_pair)
            qp.wait(bus=drive_bus, time=wait_time)
            qp.play(bus=drive_bus, waveform=drag_pair)
            qp.sync()  # this ok?
            qp.play(
                bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf)
            )  # not sure about this: is the waveform right?
            qp.acquire(bus=readout_bus)

    return qp


# Drag coefficient calibration node
drag_values = np.linspace(-3, 3, 41)

def drag_coefficient_calibration(drive_bus: str, readout_bus: str, sweep_values: List[int]):
    """The drag coefficient calibration experiment written as a QProgram.

    Args:
        drive_bus (str): Name of the drive bus
        readout_bus (str): Name of the readout bus

    Returns:
        QProgram: The QProgram describing the experiment. It will need to be compiled to be run on the qblox cluster.
    """
    
    qp = ql.QProgram()
    drag_coefficient = qp.variable(float)

    """
    Adjust the arguments of DragPulse based on the runcard.
    The 'amplitude' argument is computed as amplitude = theta*pi_pulse_amplitude/pi,
    where theta is the argument of the Drag circuit constructor and pi_pulse_amplitude
    is the amplitude of the Drag circuit written in the runcard, where all the circuit
    parameters are specified.
    """
    # We use two different drag pulses with two different amplitudes.
    drag_pair_1 = DragPulse(amplitude=0.5, duration=20, num_sigmas=4, drag_coefficient=0.0)
    drag_pair_2 = DragPulse(amplitude=1.0, duration=20, num_sigmas=4, drag_coefficient=0.0)
    
    ones_wf = Square(amplitude=1.0, duration=1000)
    zeros_wf = Square(amplitude=0.0, duration=1000)

    with qp.acquire_loop(iterations=1000):
        with qp.loop(variable=drag_coefficient, values=drag_values):
            qp.set_phase(drive_bus, 0)
            qp.play(bus=drive_bus, waveform=drag_pair_1)
            qp.set_phase(drive_bus, np.pi / 2)
            qp.play(bus=drive_bus, waveform=drag_pair_2)
            qp.sync()
            qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
            qp.acquire(bus=readout_bus)
        with qp.loop(variable=drag_coefficient, values=drag_values):
            qp.set_phase(drive_bus, np.pi / 2)
            qp.play(bus=drive_bus, waveform=drag_pair_1)
            qp.set_phase(drive_bus, 0)
            qp.play(bus=drive_bus, waveform=drag_pair_2)
            qp.sync()
            qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
            qp.acquire(bus=readout_bus)

    return qp


# Flipping experiment node
flip_values_array = np.arange(0, 20, 1)


def flipping(drive_bus: str, readout_bus: str, , sweep_values: List[int]):
    """The flipping experiment written as a QProgram.

    Args:
        drive_bus (str): Name of the drive bus
        readout_bus (str): Name of the readout bus

    Returns:
        QProgram: The QProgram describing the experiment. It will need to be compiled to be run on the qblox cluster.
    """
    
    qp = ql.QProgram()
    flip_values_array_element = qp.variable(int)
    counter = qp.variable(int)

    """
    Adjust the arguments of DragPulse based on the runcard.
    The 'amplitude' argument is computed as amplitude = theta*pi_pulse_amplitude/pi,
    where theta is the argument of the Drag circuit constructor and pi_pulse_amplitude
    is the amplitude of the Drag circuit written in the runcard, where all the circuit
    parameters are specified.
    """
    # Drag pulses played once
    drag_pair_1 = DragPulse(amplitude=0.5, duration=20, num_sigmas=4, drag_coefficient=0.0)
    drag_pair_2 = DragPulse(amplitude=0.0, duration=20, num_sigmas=4, drag_coefficient=0.0)
    drag_pair_3 = DragPulse(amplitude=1.0, duration=20, num_sigmas=4, drag_coefficient=0.0)
    # Drag pulse played repeatedly inside the loop
    looped_drag_pair = DragPulse(amplitude=1.0, duration=20, num_sigmas=4, drag_coefficient=0.0)
    ones_wf = Square(amplitude=1.0, duration=1000)
    zeros_wf = Square(amplitude=0.0, duration=1000)

    # TODO: 3 acquire_loop calls are made. Is this an issue for how data is stored?
    with qp.acquire_loop(iterations=1000):
        qp.play(bus=drive_bus, waveform=drag_pair_1)
        with qp.loop(variable=flip_values_array_element, values=flip_values_array):
            with qp.loop(variable=counter, values=np.arange(0, flip_values_array_element, 1)):
                # Play looped_drag_pair the number of times indicated by 'flip_values_array_element'
                qp.play(bus=drive_bus, waveform=looped_drag_pair)
        qp.sync()
        qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
        qp.acquire(bus=readout_bus)

    with qp.acquire_loop(iterations=1000):
        qp.play(bus=drive_bus, waveform=drag_pair_2)
        qp.sync()
        qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
        qp.acquire(bus=readout_bus)

    with qp.acquire_loop(iterations=1000):
        qp.play(bus=drive_bus, waveform=drag_pair_3)
        qp.sync()
        qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
        qp.acquire(bus=readout_bus)

    return qp


# AllXY experiment node (for initial status check and final validation)
def all_xy(drive_bus: str, readout_bus: str):
    qp = ql.QProgram()

    drag_pair = DragPulse(amplitude=1.0, duration=20, num_sigmas=4, drag_coefficient=0.0)
    zero_amplitude_drag_pair = DragPulse(amplitude=0.0, duration=20, num_sigmas=4, drag_coefficient=0.0)
    ones_wf = Square(amplitude=1.0, duration=1000)
    zeros_wf = Square(amplitude=0.0, duration=1000)

    # Load the file with the all_XY circuit settings
    all_xy_circuit_settings_path = "./all_xy_circuits.json"
    with open(all_xy_circuit_settings_path, encoding="utf8") as f:
        circuits_settings = json.load(f)

    # TODO: 21 acquire_loop calls are made. Is this an issue for how data is stored?
    for circuit_setting in circuits_settings:
        gates = circuit_setting["gates"]
        gate_parameters = circuit_setting["params"]
        for gate, gate_parameter in zip(gates, gate_parameters):
            with qp.acquire_loop(iterations=1000):
                if gate == "RX":
                    rx_gain = gate_parameter
                    rx_phase = 0
                    qp.set_gain(bus=drive_bus, gain_path0=rx_gain, gain_path1=rx_gain)
                    qp.set_phase(bus=drive_bus, phase=rx_phase)
                    qp.play(bus=drive_bus, waveform=drag_pair)
                elif gate == "RY":
                    ry_gain = gate_parameter
                    ry_phase = np.pi / 2
                    qp.set_gain(bus=drive_bus, gain_path0=ry_gain, gain_path1=ry_gain)
                    qp.set_phase(bus=drive_bus, phase=ry_phase)
                    qp.play(bus=drive_bus, waveform=drag_pair)
                elif gate == "I":
                    qp.set_phase(bus=drive_bus, phase=0)
                    qp.play(bus=drive_bus, waveform=zero_amplitude_drag_pair)

                qp.sync()
                qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
                qp.acquire(bus=readout_bus)

    return qp


######################################################################################################
"""
Define the analysis functions and plotting functions.
    - Analysis functions analyze and fit the experimental data. One analysis function could be used by more
        than one experiment.
    - Plotting functions plot the fitted data. Each fitting function has an associated plot function, because
        the labels of the plot depend on the fitting function.
"""

def analyze_rabi(datapath : str = None, fit_quadrature = "i", label=""):
    """
    Analyzes the Rabi experiment data.

    Args:
        datapath (str, optional): Path to the calibration data YAML file. If not provided, the last results file is used.
    
    Returns: 
        fitted_pi_pulse_amplitude (int)
    """
    
    # Get the path of the experimental data file
    #TODO: this will not work with my implementation, there always needs to be a datapath or a unique way to 
    # identify the right file.
    timestamp = get_last_timestamp()
    if datapath is None:
        datapath = get_last_results()
    parent_directory = os.path.dirname(datapath)
    figure_filepath = os.path.join(parent_directory, "Rabi.PNG")
    # get data
    data_raw = calibration_utils.get_raw_data(datapath)
    
    amplitude_loop_values = np.array(data_raw["loops"][0]["values"])
    swept_variable = data_raw["loops"][0]["parameter"]
    this_shape = len(amplitude_loop_values)

    # Get flattened data and shape it
    i, q = calibration_utils.get_iq_from_raw(data_raw)
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

    print(fit.params)

    optimal_parameters = [a_value, b_value, c_value, d_value]
    fitted_pi_pulse_amplitude = np.abs(1 / (2 * optimal_parameters[1]))

    # Plot
    title_label = f"{timestamp} {label}"
    fig, axes = calibration_utils.plot_iq(amplitude_loop_values, i, q, title_label, swept_variable)
    calibration_utils.plot_fit(
        amplitude_loop_values, optimal_parameters, axes[fit_signal_idx], fitted_pi_pulse_amplitude
    )
    fig.savefig(figure_filepath, format="PNG")
    return fitted_pi_pulse_amplitude

def analyze_drag_coef(datapath=None, fit_quadrature="i", label=""):
    """
    Analyzes the drag coefficient calibration experiment data.

    Args:
        datapath (str, optional): Path to the calibration data YAML file. If not provided, the last results file is used.

    Returns: 
        fitted_drag_coeff (int): The optimal drag coefficient.
    """
    
    # Get path of the experimental data file
    #TODO: this will not work with my implementation, there always needs to be a datapath or a unique way to 
    # identify the right file.
    timestamp = get_last_timestamp()
    if datapath == None:
        datapath = get_last_results()
    parent_directory = os.path.dirname(datapath)
    figure_filepath = os.path.join(parent_directory, f"Drag.PNG")
    # get data
    data_raw = calibration_utils.get_raw_data(datapath)

    parameter = data_raw["loops"][0]["parameter"]
    drag_values = data_raw["loops"][0]["values"]

    num_circuits = 2
    this_shape = (
        num_circuits,
        len(drag_values),
    )

    # Get flattened data and shape it
    i, q = calibration_utils.get_iq_from_raw(data_raw)
    i = i.reshape(this_shape)
    q = q.reshape(this_shape)

    # Process data
    use_signal = i if fit_quadrature == "i" else q
    difference = use_signal[0, :] - use_signal[1, :]

    # Fit
    def sinus(x, a, b, c, d):
        return a * np.sin(b * np.array(x) - c) + d

    a_guess = np.amax(difference) - np.amin(difference)
    
    # Sinus fit
    mod = lmfit.Model(sinus)
    mod.set_param_hint("a", value=a_guess, vary=True, min=0)
    mod.set_param_hint("b", value=0, vary=True)
    mod.set_param_hint("c", value=0, vary=True)
    mod.set_param_hint("d", value=1 / 2, vary=True, min=0)

    params = mod.make_params()
    fit = mod.fit(data=difference, params=params, x=drag_values)

    a_value = fit.params["a"].value
    b_value = fit.params["b"].value
    c_value = fit.params["c"].value
    d_value = fit.params["d"].value

    optimal_parameters = [a_value, b_value, c_value, d_value]
    # NOTE: this could be wrong. Paul will let me know. Ramiro originally added this line.
    fitted_drag_coeff = (np.arcsin(-optimal_parameters[3] / optimal_parameters[0]) + optimal_parameters[2]) / optimal_parameters[1]

    # Plot
    title_label = f"{timestamp} {label}"
    label = ["X/2 - Y", "Y/2 - X"]
    fig, axs = plt.subplots(1, 2)
    ax = axs[0]
    for _ in range(2):
        ax.plot(drag_values, use_signal[_, :], "-o", label=label[_])
    ax.set_xlabel("Drag Coefficient")
    ax.legend()

    ax = axs[1]
    func = sinus
    label_fit = f"Drag coeff = {fitted_drag_coeff:.3f}"
    ax.plot(drag_values, func(drag_values, *optimal_parameters), "--", label=label_fit, color="red")
    ax.plot(drag_values, difference, "o")
    ax.set_xlabel("Drag Coefficient")
    ax.legend()
    fig.savefig(figure_filepath, format="PNG")
    return fitted_drag_coeff

######################################################################################################
"""
Initialize all the nodes and add them to the calibration graph.
"""
"""

 """
 # TODO: unfinished, analysis missing
initial_all_xy_node = CalibrationNode(node_id="all_xy", qprogram=all_xy("drive_bus", "readout_bus"), model=None, qubit=0)
rabi_1_node = CalibrationNode(
    node_id="rabi_1", qprogram=rabi, sweep_interval=rabi_values, analysis_function=analyze_rabi, model=None, qubit=0
)
 # TODO: unfinished, analysis missing
ramsey_coarse_node = CalibrationNode(
    node_id="ramsey_coarse", qprogram=ramsey("drive_bus", "readout_bus"), sweep_intervals=wait_values, model=None, qubit=0
)
 # TODO: unfinished, analysis missing
ramsey_fine_node = CalibrationNode(
    node_id="ramsey_fine",
    qprogram=ramsey("drive_bus", "readout_bus"),
    sweep_interval=fine_if_values,
    is_refinement=True,
    model=None,
    qubit=0,
)
rabi_2_fine_node = CalibrationNode(node_id="rabi_2_coarse", qprogram=rabi, sweep_interval=rabi_values, analysis_function=analyze_rabi, model=None, qubit=0)
rabi_2_coarse_node = CalibrationNode(
    node_id="rabi_2_fine",
    qprogram=rabi, 
    sweep_interval=rabi_values,
    is_refinement=True, 
    analysis_function=analyze_rabi,
    model=None,
    qubit=0,
)
flipping_node = CalibrationNode(
    node_id="flipping",
    qprogram=flipping,
     
    analysis_function=analyze_rabi,
    model=None,
    qubit=0,
)
# TODO: unfinished: analysis missing
verification_all_xy_node = CalibrationNode(
    node_id="all_xy", qprogram=all_xy("drive_bus", "readout_bus"), model=None, qubit=0
)

calibration_graph = nx.DiGraph()
# Add nodes to the calibration graph, specifying connections

######################################################################################################
"""
Initialize the controller and start the calibration algorithm.
"""
controller = Controller(calibration_graph)

# Start automatic calibration
controller.run_calibration()
