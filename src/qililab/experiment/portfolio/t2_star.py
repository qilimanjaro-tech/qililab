"""This file contains a pre-defined version of a T2Star experiment."""
import numpy as np
from qibo.gates import RX, RY, M
from qibo.models import Circuit

from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, LoopOptions, Parameter
from qililab.utils import Loop, Wait

from .experiment_analysis import ExperimentAnalysis
from .fitting_models import Exp


class T2Star(ExperimentAnalysis, Exp):
    """Class used to run a T2* experiment on the given qubit.

    This experiment uses an X gate to excite the qubit, then waits for a certain time, then applies a Drag pulse with
    the amplitude of an RX(pi/2) gate and a variable phase, and finally measures the qubit.

    Args:
        platform (Platform): platform used to run the experiment
        qubit (int): qubit index used in the experiment
        loop_options (LoopOptions): wait time loop options
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 10000.
        hardware_average (int, optional): number of repetitions used to average the result. Defaults to 10000.
    """

    def __init__(
        self,
        platform: Platform,
        qubit: int,
        loop_options: LoopOptions,
        repetition_duration=10000,
        hardware_average=10000,
    ):
        # Define circuit used in this experiment
        circuit = Circuit(qubit)
        circuit.add(RX(qubit, theta=np.pi / 2))
        circuit.add(Wait(qubit, t=0))
        # here we should use the Drag operation of the IR
        # until then, we can use RY and loop over the Y phase
        circuit.add(RY(qubit, theta=np.pi / 2))
        circuit.add(M(qubit))

        control_bus, readout_bus = platform.get_bus_by_qubit_index(qubit)

        wait_loop = Loop(alias="0", parameter=Parameter.GATE_PARAMETER, options=loop_options)
        experiment_options = ExperimentOptions(
            name="T2*",
            loops=[wait_loop],
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
            plot_y_label="|S21| [dB]",
        )

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=[circuit],
            options=experiment_options,
            control_bus=control_bus,
            readout_bus=readout_bus,
        )
