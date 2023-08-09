"""
This file contains an example of use of the automatic calibration algorithm. 

TODO: elaborate 
"""

import os

import lmfit
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy.signal import find_peaks

import qililab as ql
import qililab.automatic_calibration.calibration_utils.calibration_utils as calibration_utils
from qililab import qprogram
from qililab.automatic_calibration.calibration_node import CalibrationNode
from qililab.automatic_calibration.controller import Controller
from qililab.platform.platform import Platform
from qililab.waveforms import DragPulse, IQPair, Square

#################################################################################################
""" Define the platform and connect to the instruments """

os.environ["RUNCARDS"] = "../runcards"
os.environ["DATA"] = f"../data"
platform_name = "soprano_master_galadriel"
platform = ql.build_platform(name=platform_name)
platform.filepath = os.path.join(os.environ["RUNCARDS"], f"{platform_name}.yml")

platform.connect()
platform.turn_on_instruments()
platform.initial_setup()
  
##################################### EXPERIMENTS ##################################################
""" Define the QPrograms, i.e. the experiments that will be the nodes of the calibration graph """


# Rabi experiment 
rabi_values = {"start": 0,
               "stop": 0.25,
               "step": (0.25-0)/40 #It's written like this because it's derived from a np.linspace definition
               }
fine_rabi_values = {"start": -0.1,
                    "stop": 0.1,
                    "step": 0.001
                    }

def rabi(drive_bus: str, readout_bus: str, sweep_values: dict):
    """The Rabi experiment written as a QProgram.

    Args:
        drive_bus (str): Name of the drive bus
        readout_bus (str): Name of the readout bus

    Returns:
        qp (QProgram): The QProgram describing the experiment. It will need to be compiled to be run on the qblox cluster.
    """
    qp = ql.QProgram()
    gain = qp.variable(float)

    # Adjust the arguments of DragPulse based on the runcard
    drag_pair = DragPulse(amplitude=1.0, duration=20, num_sigmas=4, drag_coefficient=0.0)

    ones_wf = Square(amplitude=1.0, duration=1000)
    zeros_wf = Square(amplitude=0.0, duration=1000)

    with qp.acquire_loop(iterations=1000):
        # We iterate over the gain instead of amplitude because it's equivalent and we can't iterate over amplitude.
        with qp.for_loop(variable=gain, start = sweep_values["start"], stop = sweep_values["stop"], step = sweep_values["step"]):
            qp.set_gain(bus=drive_bus, gain_path0=gain, gain_path1=gain)
            qp.play(bus=drive_bus, waveform=drag_pair)
            qp.sync()
            qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
            qp.acquire(bus=readout_bus)

    return qp


# Ramsey experiment (it's run twice to refine values)
# TODO: implement this once parallel loops are supported by qprogram
wait_values = np.arange(8.0, 1000, 20)
fine_if_values = np.arange(-2e6, 2e6, 0.2e6)


def ramsey(drive_bus: str, readout_bus: str):
    """The Ramsey experiment written as a QProgram.

    Args:
        drive_bus (str): Name of the drive bus
        readout_bus (str): Name of the readout bus

    Returns:
        qp (QProgram): The QProgram describing the experiment. It will need to be compiled to be run on the qblox cluster.
    """
    qp = ql.QProgram()
    wait_time = qp.variable(int)

    drag_pair = DragPulse(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=1.2)
    ones_wf = Square(amplitude=1.0, duration=1000)
    zeros_wf = Square(amplitude=0.0, duration=1000)

    with qp.acquire_loop(iterations=1000):
        with qp.for_loop(variable=wait_time, values=wait_values):
            qp.play(bus=drive_bus, waveform=drag_pair)
            qp.wait(bus=drive_bus, time=wait_time)
            qp.play(bus=drive_bus, waveform=drag_pair)
            qp.sync()  # this ok?
            qp.play(
                bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf)
            )  # not sure about this: is the waveform right?
            qp.acquire(bus=readout_bus)

    return qp


# Drag coefficient calibration experiment
drag_values = {"start": -3,
               "stop": 3,
               "step": 0.15
               }


def drag_coefficient_calibration(drive_bus: str, readout_bus: str, sweep_values: dict):
    """The drag coefficient calibration experiment written as a QProgram.

    Args:
        drive_bus (str): Name of the drive bus
        readout_bus (str): Name of the readout bus

    Returns:
        qp (QProgram): The QProgram describing the experiment. It will need to be compiled to be run on the qblox cluster.
    """

    qp = ql.QProgram()
    drag_coefficient = qp.variable(float)

    """
    NOTE: User should adjust the arguments of DragPulse based on the runcard.
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
        with qp.for_loop(variable=drag_coefficient, start = sweep_values["start"], stop = sweep_values["stop"], step = sweep_values["step"]):
            qp.set_phase(drive_bus, 0)
            qp.play(bus=drive_bus, waveform=drag_pair_1)
            qp.set_phase(drive_bus, np.pi / 2)
            qp.play(bus=drive_bus, waveform=drag_pair_2)
            qp.sync()
            qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
            qp.acquire(bus=readout_bus)
        with qp.for_loop(variable=drag_coefficient, start = drag_values["start"], stop = drag_values["stop"], step = drag_values["step"]):
            qp.set_phase(drive_bus, np.pi / 2)
            qp.play(bus=drive_bus, waveform=drag_pair_1)
            qp.set_phase(drive_bus, 0)
            qp.play(bus=drive_bus, waveform=drag_pair_2)
            qp.sync()
            qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
            qp.acquire(bus=readout_bus)

    return qp


# Flipping experiment 
flip_values_array = {"start": 0,
                    "stop": 20,
                    "step": 1
                    }


def flipping(drive_bus: str, readout_bus: str, sweep_values: list[int]):
    """The flipping experiment written as a QProgram.

    Args:
        drive_bus (str): Name of the drive bus
        readout_bus (str): Name of the readout bus

    Returns:
        qp (QProgram): The QProgram describing the experiment. It will need to be compiled to be run on the qblox cluster.
    """

    qp = ql.QProgram()
    flip_values_array_element = qp.variable(int)
    counter = qp.variable(int)

    """
    NOTE: User should adjust the arguments of DragPulse based on the runcard.
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

    with qp.acquire_loop(iterations=1000):
        qp.play(bus=drive_bus, waveform=drag_pair_1)
        with qp.for_loop(variable=flip_values_array_element, start = sweep_values["start"], stop = sweep_values["stop"], step = sweep_values["step"]):
            with qp.for_loop(variable=counter, start = 0, stop = flip_values_array_element, step = 1):
                # Play looped_drag_pair the number of times indicated by 'flip_values_array_element'
                qp.play(bus=drive_bus, waveform=looped_drag_pair)
                qp.play(bus=drive_bus, waveform=looped_drag_pair)
        qp.sync()
        qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
        qp.acquire(bus=readout_bus)

        qp.play(bus=drive_bus, waveform=drag_pair_2)
        qp.sync()
        qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
        qp.acquire(bus=readout_bus)
    
        qp.play(bus=drive_bus, waveform=drag_pair_3)
        qp.sync()
        qp.play(bus=readout_bus, waveform=IQPair(I=ones_wf, Q=zeros_wf))
        qp.acquire(bus=readout_bus)

    return qp


# AllXY experiment node (for initial status check and final validation)
def all_xy(drive_bus: str, readout_bus: str):
    """The allXY experiment written as a QProgram.

    Args:
        drive_bus (str): Name of the drive bus
        readout_bus (str): Name of the readout bus

    Returns:
        qp (QProgram): The QProgram describing the experiment. It will need to be compiled to be run on the qblox cluster.
    """
    qp = ql.QProgram()

    drag_pair = DragPulse(amplitude=1.0, duration=20, num_sigmas=4, drag_coefficient=0.0)
    zero_amplitude_drag_pair = DragPulse(amplitude=0.0, duration=20, num_sigmas=4, drag_coefficient=0.0)
    ones_wf = Square(amplitude=1.0, duration=1000)
    zeros_wf = Square(amplitude=0.0, duration=1000)

    # Definition of the all_xy sequence:
    circuits_settings = [
        {"name": "II", "gates": ["I", "I", "M"], "params": [-1, -1, -1]},
        {"name": "XpXp", "gates": ["RX", "RX", "M"], "params": [1, 1, -1]},
        {"name": "YpYp", "gates": ["RY", "RY", "M"], "params": [1, 1, -1]},
        {"name": "XpYp", "gates": ["RX", "RY", "M"], "params": [1, 1, -1]},
        {"name": "YpXp", "gates": ["RY", "RX", "M"], "params": [1, 1, -1]},
        {"name": "X9I", "gates": ["RX", "I", "M"], "params": [0.5, -1, -1]},
        {"name": "Y9I", "gates": ["RY", "I", "M"], "params": [0.5, -1, -1]},
        {"name": "X9Y9", "gates": ["RX", "RY", "M"], "params": [0.5, 0.5, -1]},
        {"name": "Y9X9", "gates": ["RY", "RX", "M"], "params": [0.5, 0.5, -1]},
        {"name": "X9Yp", "gates": ["RX", "RY", "M"], "params": [0.5, 1, -1]},
        {"name": "Y9Xp", "gates": ["RY", "RX", "M"], "params": [0.5, 1, -1]},
        {"name": "XpY9", "gates": ["RX", "RY", "M"], "params": [1, 0.5, -1]},
        {"name": "YpX9", "gates": ["RY", "RX", "M"], "params": [1, 0.5, -1]},
        {"name": "X9Xp", "gates": ["RX", "RX", "M"], "params": [0.5, 1, -1]},
        {"name": "XpX9", "gates": ["RX", "RX", "M"], "params": [1, 0.5, -1]},
        {"name": "Y9Yp", "gates": ["RY", "RY", "M"], "params": [0.5, 1, -1]},
        {"name": "YpY9", "gates": ["RY", "RY", "M"], "params": [1, 0.5, -1]},
        {"name": "XpI", "gates": ["RX", "I", "M"], "params": [1, -1, -1]},
        {"name": "YpI", "gates": ["RY", "I", "M"], "params": [1, -1, -1]},
        {"name": "X9X9", "gates": ["RX", "RX", "M"], "params": [0.5, 0.5, -1]},
        {"name": "Y9Y9", "gates": ["RY", "RY", "M"], "params": [0.5, 0.5, -1]},
    ]

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


######################################### ANALYSIS ###################################################
"""
Define the analysis functions and plotting functions.
    - Analysis functions analyze and fit the experimental data. One analysis function could be used by more
        than one experiment.
    - Plotting functions plot the fitted data.
NOTE: For now, each experiment has it own custom function that handled both analysis (=processing and fitting the data) and plotting. 
        This will be made less hardcoded in the future by another intern.
"""

def analyze_rabi(datapath, fit_quadrature="i", label=""):
    """
    Analyzes the Rabi experiment data.

    Args:
        datapath: Where the data experimental is stored. If it's a string, it represents the path of a file. Otherwise it's something else, a python object (like a list).

    Returns:
        fitted_pi_pulse_amplitude (int)
    """

    # Get the path of the experimental data file
    # TODO: this will not work with my implementation, there always needs to be a datapath or a unique way to
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


def analyze_ramsey(datapath, fit_quadrature="i", label="", prominence_peaks=20, analyze=True):
    """
    Analyzes the ramsey experiment data.

    Args:
        datapath: Where the data experimental is stored. If it's a string, it represents the path of a file. Otherwise it's something else, a python object (like a list).

    Returns:
        The optimal frequency found with the Ramsey experiment.
    """
    # Get the path of the experimental data file
    # TODO: this will not work with my implementation, there always needs to be a datapath or a unique way to
    # identify the right file.
    timestamp = get_last_timestamp()
    if datapath == None:
        datapath = get_last_results()
    parent_directory = os.path.dirname(datapath)
    figure_filepath = os.path.join(parent_directory, f"RamseyFreq.PNG")
    # get data
    data_raw = get_raw_data(datapath)

    # This is experiment specific and will go differently for every scheme of sweeps for tune-up
    freq_loop_values = np.array(data_raw["loops"][0]["values"])
    freq_label = data_raw["loops"][0]["parameter"]

    wait_loop_values = np.array(data_raw["loops"][0]["loop"]["values"])
    wait_label = data_raw["loops"][0]["loop"]["parameter"]
    this_shape = (len(freq_loop_values), len(wait_loop_values))

    # get flattened data and shape it
    i, q = calibration_utils.get_iq_from_raw(data_raw)
    i = i.reshape(this_shape)
    q = q.reshape(this_shape)

    # parse data and transform it
    signal_vec = i if fit_quadrature == "i" else q
    peaks_idx = []

    fft_x = np.fft.fftfreq(
        n=len(signal_vec[0, :]),
        d=wait_loop_values[1] - wait_loop_values[0],
    )
    mask_fft = np.argsort(fft_x)
    fft_x_sorted = fft_x[mask_fft]
    x_axis = fft_x_sorted
    y_axis = freq_loop_values
    z_axis = []
    if analyze:
        for ii, freq in enumerate(freq_loop_values):
            fft_y = np.fft.fft(signal_vec[ii, :] - np.mean(signal_vec[ii, :]))
            # sort
            fft_y_sorted = fft_y[mask_fft]
            # normalize
            this_norm = np.sqrt(np.sum(np.abs(fft_y_sorted) ** 2))
            # fft_y_sorted = fft_y_sorted/this_norm

            peak, _ = find_peaks(np.abs(fft_y_sorted), prominence=prominence_peaks)
            if len(peak) == 2:
                peaks_idx.append(peak)
            else:
                peaks_idx.append([np.nan, np.nan])
            z_axis.append(fft_y_sorted)

        peaks_idx = np.array(peaks_idx)
        nan_indexes = np.argwhere(np.isnan(peaks_idx))
        nan_indexes = nan_indexes[:, 0]
        clean_array = np.delete(peaks_idx, nan_indexes, axis=0)
        y_axis_fit = np.delete(y_axis, nan_indexes, axis=0)
        clean_array = clean_array.astype(np.int64)

        peaks_x = np.array([fft_x_sorted[p] for p in clean_array[:, 1]])

        # Fit
        def absline(x, a, xc):
            return np.abs(a * (x - xc))

        absmod = lmfit.Model(absline)
        absmod.set_param_hint(
            name="a",
            value=(np.max(peaks_x) - np.min(peaks_x)) / (np.max(y_axis_fit) - np.min(y_axis_fit)),
        )
        absmod.set_param_hint(name="xc", value=np.mean(y_axis_fit))
        params = absmod.make_params()
        fit_res = absmod.fit(x=y_axis_fit, data=peaks_x, params=params)
        fit_x = np.linspace(y_axis_fit[0], y_axis_fit[-1], num=101)
        fit_y = absline(fit_x, **fit_res.best_values)
    else:
        for ii, freq in enumerate(freq_loop_values):
            fft_y = np.fft.fft(signal_vec[ii, :] - np.mean(signal_vec[ii, :]))
            # sort
            fft_y_sorted = fft_y[mask_fft]
            z_axis.append(fft_y_sorted)

    # Plot
    title_label = f"{timestamp} {label}"
    fig, ax = plt.subplots()
    plt.pcolormesh(x_axis, y_axis, np.abs(z_axis), label="FFT Data")
    if analyze:
        ax.plot(fit_y, fit_x, "r-")
        ax.plot(peaks_x, y_axis_fit, "ro", label="Data")
        ax.axhline(
            fit_res.best_values["xc"],
            linestyle="--",
            color="r",
            label=f"Fit={fit_res.best_values['xc']*1e-9:.5f} GHz",
        )

    ax.legend()
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Detuning")
    ax.set_title(title_label)
    fig.savefig(figure_filepath, format="PNG")
    return fit_res.best_values["xc"] if analyze else None


def analyze_drag_coefficient(datapath, fit_quadrature="i", label=""):
    """
    Analyzes the drag coefficient calibration experiment data.

    Args:
        datapath: Where the data experimental is stored. If it's a string, it represents the path of a file. Otherwise it's something else, a python object (like a list).

    Returns:
        fitted_drag_coeff (int): The optimal drag coefficient.
    """

    # Get path of the experimental data file
    # TODO: this will not work with my implementation, there always needs to be a datapath or a unique way to
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
    # This experiment returns two sine waves. We want to find their intersection, which is the optimal drag coefficient. The following formula gives us that.
    fitted_drag_coeff = (
        np.arcsin(-optimal_parameters[3] / optimal_parameters[0]) + optimal_parameters[2]
    ) / optimal_parameters[1]

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


def analyze_flipping(datapath, flips_values, fit_quadrature="i", label=""):
    """
    Analyzes the flipping experiment data.

    Args:
        datapath: Where the data experimental is stored. If it's a string, it represents the path of a file. Otherwise it's something else, a python object (like a list).

    """

    # Get path of the experimental data file
    # TODO: this will not work with my implementation, there always needs to be a datapath or a unique way to
    # identify the right file.
    timestamp = get_last_timestamp()
    if datapath == None:
        datapath = get_last_results()
    parent_directory = os.path.dirname(datapath)
    figure_filepath = os.path.join(parent_directory, f"Flipping.PNG")
    # get data
    data_raw = get_raw_data(datapath)

    # Get flattened data and shape it
    i, q = calibration_utils.get_iq_from_raw(data_raw)
    i = np.array(i).flatten()
    q = np.array(q).flatten()

    # Process data
    use_signal = i if fit_quadrature == "i" else q
    calibration_points = use_signal[-2:]
    voltage_data = use_signal[:-2]

    data_range = calibration_points[1] - calibration_points[0]
    scaled_data = [(x - calibration_points[0]) / data_range for x in voltage_data]

    # Fit
    def sinus(x, a, b, c, d):
        return a * np.sin(b * np.array(x) - c) + d

    a_guess = np.amax(scaled_data) - np.amin(scaled_data)

    # Sinus fit
    mod = lmfit.Model(sinus)
    mod.set_param_hint("a", value=a_guess, vary=True, min=0)
    mod.set_param_hint("b", value=0, vary=True)
    mod.set_param_hint("c", value=0, vary=True)
    mod.set_param_hint("d", value=1 / 2, vary=True, min=0)

    params = mod.make_params()
    fit = mod.fit(data=scaled_data, params=params, x=flips_values)

    a_value = fit.params["a"].value
    b_value = fit.params["b"].value
    c_value = fit.params["c"].value
    d_value = fit.params["d"].value

    popt = [a_value, b_value, c_value, d_value]

    epsilon_coef = popt[1] / 2
    reduced_chi = fit.redchi

    # Line fit
    def line(x, a, b):
        return a * x + b

    mod2 = lmfit.Model(line)
    mod2.set_param_hint("a", value=-1, vary=True)
    mod2.set_param_hint("b", value=0.5, vary=True)

    params2 = mod2.make_params()
    fit2 = mod2.fit(data=scaled_data, params=params2, x=flips_values)

    a_value2 = fit2.params["a"].value
    b_value2 = fit2.params["b"].value

    popt2 = [a_value2, b_value2]

    epsilon_coef2 = popt2[0] / 2
    reduced_chi2 = fit2.redchi

    # Plot
    title_label = f"{timestamp} {label}"
    fig, axs = plt.subplots(1, 2)
    ax = axs[0]
    ax.plot(flips_values, scaled_data, "--o", label="data")
    ax.plot(flips_values[-1] + 1, 1, "o", label="1")
    ax.plot(flips_values[-1] + 1, 0, "o", label="0")
    ax.set_xlabel("Number of Flips")
    ax.legend()

    ax = axs[1]
    if reduced_chi < reduced_chi2:
        func = sinus
        label_fit = rf"$\epsilon$ = {epsilon_coef:.3f}"
        ax.plot(flips_values, func(flips_values, *popt), "--", label=label_fit, color="red")
    else:
        func = line
        label_fit = rf"$\epsilon$ = {epsilon_coef2:.3f}"
        ax.plot(flips_values, func(flips_values, *popt2), "--", label=label_fit, color="red")

    ax.plot(flips_values, scaled_data, "--o")
    ax.plot(flips_values[-1] + 1, 1, "o", label="1")
    ax.plot(flips_values[-1] + 1, 0, "o", label="0")
    ax.set_xlabel("Number of Flips")
    ax.legend()
    fig.savefig(figure_filepath, format="PNG")

    return epsilon_coef if reduced_chi < reduced_chi2 else epsilon_coef2

def analyze_all_xy(datapath, label=""):
    """
    Analyzes the AllXY experiment data.

    Args:
        datapath: Where the data experimental is stored. If it's a string, it represents the path of a file. Otherwise it's something else, a python object (like a list).

    Returns:
        The plot of the AllXY experiment data
    """

    # Get the path of the experimental data file
    # TODO: this will not work with my implementation, there always needs to be a datapath or a unique way to
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

    plt.clf()
    plt.figure()
    plt.plot(i, "-o")
    ax = plt.gca()
    ax.set_title( "tbd" + ax.get_title()) #TODO: add timestamp in title?
    #TODO: save figure with appropriate path
    #TODO: print figure to show user
    
######################################################################################################
"""
Initialize all the nodes and add them to the calibration graph. Add edges to calibration graph.

Example of interpretation of an edge: 
   node1 <---- node2    means "node2 depends on node1"
"""

all_xy_node_1 = CalibrationNode(
    node_id="all_xy_1", 
    qprogram=all_xy, 
    analysis_function=analyze_all_xy, 
    qubit=0
)
rabi_1_node = CalibrationNode(
    node_id="rabi_1", qprogram=rabi, sweep_interval=rabi_values, analysis_function=analyze_rabi, qubit=0
)
ramsey_coarse_node = CalibrationNode(
    node_id="ramsey_coarse",
    qprogram=ramsey("drive_bus", "readout_bus"),
    sweep_intervals=wait_values,
    analysis_function=analyze_ramsey,
    qubit=0,
)
ramsey_fine_node = CalibrationNode(
    node_id="ramsey_fine",
    qprogram=ramsey("drive_bus", "readout_bus"),
    sweep_interval=fine_if_values,
    is_refinement=True,
    analysis_function=analyze_ramsey,
    qubit=0,
)
drag_coefficient_node = CalibrationNode(
    node_id="drag",
    qprogram=drag_coefficient_calibration,
    sweep_interval=drag_values,
    analysis_function=analyze_drag_coefficient,
    qubit=0,
)
rabi_2_coarse_node = CalibrationNode(
    node_id="rabi_2_coarse",
    qprogram=rabi,
    sweep_interval=rabi_values,
    analysis_function=analyze_rabi,
    qubit=0,
)
rabi_2_fine_node = CalibrationNode(
    node_id="rabi_2_fine",
    qprogram=rabi,
    sweep_interval=rabi_values,
    is_refinement=True,
    analysis_function=analyze_rabi,
    qubit=0,
)
flipping_node = CalibrationNode(
    node_id="flipping",
    qprogram=flipping,
    analysis_function=analyze_flipping,
    qubit=0,
)
all_xy_node_2 = CalibrationNode(
    node_id="all_xy_2", 
    qprogram=all_xy, 
    analysis_function=analyze_all_xy, 
    qubit=0
)

calibration_graph = nx.DiGraph()

nodes = [
    all_xy_node_1,
    rabi_1_node,
    ramsey_coarse_node,
    ramsey_fine_node,
    drag_coefficient_node,
    rabi_2_coarse_node,
    rabi_2_fine_node,
    flipping_node,
    all_xy_node_2
]

calibration_graph.add_nodes_from(nodes)
    
calibration_graph.add_edge(all_xy_node_2, flipping_node)
calibration_graph.add_edge(flipping_node, rabi_2_fine_node)
calibration_graph.add_edge(rabi_2_fine_node, rabi_2_coarse_node)
calibration_graph.add_edge(rabi_2_coarse_node, drag_coefficient_node)
calibration_graph.add_edge(drag_coefficient_node, ramsey_fine_node)
calibration_graph.add_edge(ramsey_fine_node, ramsey_coarse_node)
calibration_graph.add_edge(ramsey_coarse_node, rabi_1_node)
calibration_graph.add_edge(rabi_1_node, all_xy_node_1)
######################################################################################################
"""
Initialize the controller and start the calibration algorithm.
"""
controller = Controller(calibration_graph)

# Start automatic calibration
controller.run_calibration()
