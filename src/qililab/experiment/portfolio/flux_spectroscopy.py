"""This file contains a pre-defined version of a rabi experiment."""
import numpy as np
from qibo.gates import M
from qibo.models import Circuit

from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop

from .experiment_analysis import ExperimentAnalysis
from .fitting_models import CosFunc


class FluxSpectroscopy(ExperimentAnalysis, CosFunc):
    """Class used to run a flux spectroscopy experiment on the given qubit. This experiment modifies the amplitude of the pulse
    associated to the X gate.

    Args:
        platform (Platform): platform used to run the experiment
        qubit (int): qubit index used in the experiment
        offset_loop_values (numpy.ndarray): array of values to loop through in the experiment. Modifies the offset of the bus connected to the flux line
        frequency_loop_values (numpy.ndarray): array of values to loop through in the experiment. Modifies the frequency of the readout bus
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 10000.
        hardware_average (int, optional): number of repetitions used to average the result. Defaults to 10000.
    """

    def __init__(
        self,
        platform: Platform,
        qubit: int,
        offset_loop_values: np.ndarray,
        frequency_loop_values: np.ndarray,
        repetition_duration=10000,
        hardware_average=10000,
    ):
        # Get buses associated with the qubit
        control_bus, readout_bus = platform.get_bus_by_qubit_index(qubit)

        # Define circuit used in this experiment
        circuit = Circuit(1)
        circuit.add(M(qubit))

        # Define loop used in the experiment
        frequency_loop = Loop(alias=readout_bus.alias, parameter=Parameter.LO_FREQUENCY, values=frequency_loop_values)
        offset_loop = Loop(
            alias=f"flux_line_q{qubit}_bus",
            parameter=Parameter.OFFSET_OUT2,
            values=offset_loop_values,
            loop=frequency_loop,
            channel_id=1,
        )

        # Define the experiment options
        experiment_options = ExperimentOptions(
            name="Flux Spectroscopy",
            loops=[offset_loop],
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
