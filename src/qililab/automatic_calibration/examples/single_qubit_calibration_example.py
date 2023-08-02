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


# Node 1: Rabi experiment
def rabi(drive_bus: str, readout_bus: str):
    """The rabi experiment written as a QProgram.

    Args:
        drive_bus (str): Name of the drive bus
        readout_bus (str): Name of the readout bus

    Returns:
        QProgram: The QProgram describing the experiment. It will need to be compiled to be run on the qblox cluster.
    """
    qp = ql.QProgram()
    amplitude = qp.variable(float)

    drag_pair = DragPulse(amplitude=amplitude, duration=40, num_sigmas=4, drag_coefficient=1.2)
    ones_wf = Square(amplitude=1.0, duration=1000)
    zeros_wf = Square(amplitude=0.0, duration=1000)

    with qp.acquire_loop(iterations=1000):
        # TODO: Change the following to make it iterate over gain instead of amplitude
        with qp.loop(variable=amplitude, values=np.arange(0, 1, 101)):
            qp.play(bus=drive_bus, waveform=drag_pair)
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
rabi_coarse = CalibrationNode(name="rabi_coarse", qprogram=rabi("drive_bus", "readout_bus"), model=cosine, qubit=0)
rabi_mid = CalibrationNode(name="rabi_coarse", qprogram=rabi("drive_bus", "readout_bus"), model=cosine, qubit=0)
# more nodes ...

calibration_graph = nx.DiGraph()
# Add nodes to the calibration graph, specifying connections

######################################################################################################
"""
Initialize the controller and start the calibration algorithm.
"""
controller = Controller(calibration_graph)

# Start automatic calibration
controller.run_calibration()
