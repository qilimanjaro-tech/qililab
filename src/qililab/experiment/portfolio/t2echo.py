"""This file contains a pre-defined version of the flux spectroscopy experiment."""
import numpy as np
from qibo.gates import M
from qibo.models import Circuit

import qililab as ql
from qililab.experiment.portfolio import Exp, ExperimentAnalysis
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop, Wait


class T2Echo(ExperimentAnalysis, Exp):
    def __init__(
        self,
        qubit: int,
        platform: Platform,
        wait_loop_values: np.ndarray,
        repetition_duration=10000,
        measurement_buffer=100,
        hardware_average=10000,
    ):
        # Define Circuit to execute
        circuit = Circuit(qubit + 1)
        circuit.add(ql.Drag(q=qubit, theta=np.pi / 2, phase=0))
        circuit.add(Wait(qubit, t=0))
        circuit.add(ql.Drag(q=qubit, theta=np.pi, phase=0))
        circuit.add(Wait(qubit, t=0))
        circuit.add(ql.Drag(q=qubit, theta=np.pi / 2, phase=0))
        circuit.add(Wait(qubit, t=measurement_buffer))
        circuit.add(M(qubit))

        # Alias of loops reference the wait parameters, looping over wait times.
        first_wait_loop = Loop(alias="2", parameter=Parameter.GATE_PARAMETER, values=wait_loop_values)
        second_wait_loop = Loop(alias="5", parameter=Parameter.GATE_PARAMETER, values=wait_loop_values)

        experiment_options = ExperimentOptions(
            name="t2echo",
            loops=[first_wait_loop, second_wait_loop],
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
        )

        super().__init__(
            platform=platform,
            circuits=[circuit],
            options=experiment_options,
        )
