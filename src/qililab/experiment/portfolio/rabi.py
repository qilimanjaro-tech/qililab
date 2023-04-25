"""This file contains a pre-defined version of a rabi experiment."""
from qibo.gates import M, X
from qibo.models import Circuit

from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, LoopOptions, Parameter
from qililab.utils import Loop

from .experiment_analysis import ExperimentAnalysis
from .fitting_models import Cos


class Rabi(ExperimentAnalysis, Cos):
    """Class used to run a rabi experiment on the given qubit. This experiment modifies the amplitude of the pulse
    associated to the X gate.

    Args:
        platform (Platform): platform used to run the experiment
        qubit (int): qubit index used in the experiment
        loop_options (LoopOptions): options of the loop used in the experiment, which modifies the amplitude of X gate
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
        circuit = Circuit(1)
        circuit.add(X(qubit))
        circuit.add(M(qubit))

        control_bus, readout_bus = platform.get_bus_by_qubit_index(qubit)

        # Define loop used in the experiment
        loop = Loop(alias="X", parameter=Parameter.AMPLITUDE, options=loop_options)

        experiment_options = ExperimentOptions(
            name="Rabi",
            loops=[loop],
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
