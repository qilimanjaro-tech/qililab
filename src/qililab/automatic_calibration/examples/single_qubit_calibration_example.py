import json

import networkx as nx
import numpy as np

import qililab as ql
from qililab import qprogram
from qililab.automatic_calibration.calibration_node import CalibrationNode
from qililab.automatic_calibration.controller import Controller
from qililab.platform.platform import Platform
from qililab.waveforms import DragPulse, IQPair, Square

# Create the nodes for a calibration graph

#################################################################################################
""" Define the platform """

# TODO: Define platform configuration to pass it to Controller as argument
platform = Platform()

######################################################################################################
""" Define the QPrograms, i.e. the experiments that will be the nodes of the calibration graph """


# Rabi experiment node
amp_values = np.linspace(0, 0.25, 41)
fine_rabi_values = np.arange(-0.1, 0.1, 0.001)


def rabi(drive_bus: str, readout_bus: str):
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
        with qp.loop(variable=gain, values=amp_values):
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


def drag_coefficient_calibration(drive_bus: str, readout_bus: str):
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


def flipping(drive_bus: str, readout_bus: str):
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

    # TODO: check with Vyron: I'm not sure this is a good translation from single_qb_calibration.py: they divide it into 3 circuits there and run them sequentially
    # Here I replicate that by running the first circuit's equivalent, then acquiring, then second circuit's equivalent, acquiring, etc. I'm not sure if it's necessary
    # or correct to do these 3 separate acquisitions.
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


# AllXY experiment node (for final validation)
def all_xy(drive_bus: str, readout_bus: str, circuit_settings_path):
    qp = ql.QProgram()

    drag_pair = DragPulse(amplitude=1.0, duration=20, num_sigmas=4, drag_coefficient=0.0)
    zero_amplitude_drag_pair = DragPulse(amplitude=0.0, duration=20, num_sigmas=4, drag_coefficient=0.0)
    ones_wf = Square(amplitude=1.0, duration=1000)
    zeros_wf = Square(amplitude=0.0, duration=1000)

    # TODO: check if this json file is a universal way to store circuit settings or just a HW gimmick.
    # If it's universal, handle the fact that this function takes the path of this json as argument.
    with open(circuit_settings_path, encoding="utf8") as f:
        circuits_settings = json.load(f)

    # TODO: check with vyron if this is the right way to render the loop over gates and gate parameters,
    # by adding a acquire_loop block at each iteration.
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


def analyze_rabi():
    pass


######################################################################################################
"""
Initialize all the nodes and add them to the calibration graph.
"""
"""

 """
initial_all_xy_node = CalibrationNode(node_id="all_xy", qprogram=all_xy("drive_bus", "readout_bus"), model=idk, qubit=0)
rabi_1_node = CalibrationNode(
    node_id="rabi", qprogram=rabi("drive_bus", "readout_bus"), sweep_intervals=amp_values, model=idk, qubit=0
)
ramsey_coarse_node = CalibrationNode(
    node_id="ramsey", qprogram=ramsey("drive_bus", "readout_bus"), sweep_intervals=wait_values, model=idk, qubit=0
)
ramsey_fine_node = CalibrationNode(
    node_id="ramsey",
    qprogram=ramsey("drive_bus", "readout_bus"),
    sweep_interval=fine_if_values,
    is_refinement=True,
    model=idk,
    qubit=0,
)
rabi_2_fine_node = CalibrationNode(node_id="rabi", qprogram=rabi("drive_bus", "readout_bus"), model=idk, qubit=0)
rabi_2_coarse_node = CalibrationNode(
    node_id="rabi",
    qprogram=rabi("drive_bus", "readout_bus"),
    sweep_interval=fine_rabi_values,
    is_refinement=True,
    model=idk,
    qubit=0,
)
flipping_node = CalibrationNode(
    node_id="flipping",
    qprogram=flipping("drive_bus", "readout_bus"),
    sweep_intervals=flip_values_array,
    model=idk,
    qubit=0,
)
verification_all_xy_node = CalibrationNode(
    node_id="all_xy", qprogram=all_xy("drive_bus", "readout_bus"), model=idk, qubit=0
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
