"""This file contains a pre-defined version of a ssro experiment."""
import numpy as np
from qibo.gates import M
from qibo.models import Circuit

from qililab.experiment.portfolio import Cos, ExperimentAnalysis
from qililab.platform import Platform
from qililab.transpiler.native_gates import Drag
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop, Wait


class SSRO(ExperimentAnalysis, Cos):
    """Experiment to perform SSRO to a qubit.

    The SSRO is measured through the following sequence of operations:
        ...

    Args:
        platform (Platform): platform used to run the experiment
        qubit (int): qubit index used in the experiment
        wait_loop_values (numpy.ndarray): array of values to loop through in the experiment, which modifies the t parameter of the Wait gate
        loop_parameter (Parameter | None):
        loop_values (numpy.ndarray):
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 200000.
        hardware_average (int, optional): number of repetitions used to average the result. Default to 1.
        measurment_buffer (int, optional): time to wait before taking a measurment. Defaults to 100.
        num_bins (int, optional): number of bins of the Experiment. Defaults to 2000.
    """

    def __init__(
        self,
        qubit: int,
        platform: Platform,
        loop_parameter: Parameter | None,
        loop_values: np.ndarray,
        repetition_duration=200_000,
        hardware_average=1,
        measurement_buffer=100,
        num_bins=2_000,
    ):
        self.qubit = qubit
        self.loop_parameter = loop_parameter
        self.loop_values = loop_values

        circuit1 = Circuit(qubit + 1)
        circuit1.add(Drag(qubit, theta=0, phase=0))
        circuit1.add(Wait(qubit, t=measurement_buffer))
        circuit1.add(M(qubit))

        circuit2 = Circuit(qubit + 1)
        circuit2.add(Drag(qubit, theta=np.pi, phase=0))
        circuit2.add(Wait(qubit, t=measurement_buffer))
        circuit2.add(M(qubit))

        qubit_sequencer_mapping = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}
        sequencer = qubit_sequencer_mapping[qubit]

        if loop_parameter == Parameter.AMPLITUDE:
            loop = Loop(alias=f"M({qubit})", parameter=Parameter.AMPLITUDE, values=loop_values)
        elif loop_parameter == Parameter.IF:
            loop = Loop(alias="feedline_bus", parameter=Parameter.IF, values=loop_values, channel_id=sequencer)
        elif loop_parameter == Parameter.LO_FREQUENCY:
            loop = Loop(alias="rs_1", parameter=Parameter.LO_FREQUENCY, values=loop_values, channel_id=None)
        elif loop_parameter == Parameter.DURATION:
            loop = Loop(alias=f"M({qubit})", parameter=Parameter.DURATION, values=loop_values)
            loop2 = Loop(
                alias="feedline_bus", parameter=Parameter.INTEGRATION_LENGTH, values=loop_values, channel_id=qubit
            )
        elif loop_parameter == Parameter.ATTENUATION:
            loop = Loop(alias="attenuator", parameter=Parameter.ATTENUATION, values=loop_values)

        elif loop_parameter is None:
            loop = Loop(alias="external", parameter=Parameter.EXTERNAL, values=np.array([1]))

        experiment_options = ExperimentOptions(
            name="ssro",
            loops=[loop, loop2] if loop_parameter == Parameter.DURATION else [loop],
            settings=ExperimentSettings(
                repetition_duration=repetition_duration, hardware_average=hardware_average, num_bins=num_bins
            ),
        )

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=[circuit1, circuit2],
            options=experiment_options,
        )
