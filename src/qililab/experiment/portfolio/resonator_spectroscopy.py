"""This file contains a pre-defined version of a resonator spectroscopy experiment."""
import numpy as np
from qibo.gates import M
from qibo.models import Circuit

from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop

from .experiment_analysis import ExperimentAnalysis
from .fitting_models import Cos


class ResonatorSpectroscopy(ExperimentAnalysis, Cos):
    """Class used to run a resonator spectroscopy experiment on the given qubit.

    This experiment modifies the LO frequency of the SignalGenerator instrument connected to the resonator of the
    given qubit.

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
        loop_values: np.ndarray,
        repetition_duration=10000,
        hardware_average=10000,
    ):
        # Define circuit used in this experiment
        circuit = Circuit(1)
        circuit.add(M(qubit))

        control_bus, readout_bus = platform.get_bus_by_qubit_index(qubit)

        # Set sync to False, because we are only using the readout bus
        readout_bus.set_parameter(parameter=Parameter.SYNC_ENABLED, value=False)

        # Define loop used in the experiment
        loop = Loop(alias=readout_bus.alias, parameter=Parameter.LO_FREQUENCY, values=loop_values)

        experiment_options = ExperimentOptions(
            name="ResonatorSpectroscopy",
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
