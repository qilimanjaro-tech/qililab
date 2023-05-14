"""This file contains a pre-defined version of a T1 experiment."""
import numpy as np
from qibo.gates import M, X
from qibo.models import Circuit

from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop, Wait

from .experiment_analysis import ExperimentAnalysis
from .fitting_models import Exp


class T1(ExperimentAnalysis, Exp):
    """Class used to run a T1 experiment on the given qubit.

    This experiment uses an X gate to excite the qubit, and then waits for a given time before measuring the qubit.

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
        loop_values: np.ndarray,
        repetition_duration=10000,
        hardware_average=10000,
    ):
        # Define circuit used in this experiment
        circuit = Circuit(qubit)
        circuit.add(X(qubit))
        circuit.add(Wait(qubit, t=0))
        circuit.add(M(qubit))

        control_bus, readout_bus = platform.get_bus_by_qubit_index(qubit)

        wait_loop = Loop(alias="0", parameter=Parameter.GATE_PARAMETER, values=loop_values)
        experiment_options = ExperimentOptions(
            name="T1",
            loops=[wait_loop],
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
        )

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=[circuit],
            options=experiment_options,
            control_bus=control_bus,
            readout_bus=readout_bus,
        )
