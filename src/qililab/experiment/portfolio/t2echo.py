"""This file contains a pre-defined version of the flux spectroscopy experiment."""
import matplotlib.pyplot as plt
import numpy as np
from lmfit.models import Model
from qibo.gates import M
from qibo.models import Circuit

import qililab as ql
from qililab.experiment.portfolio import Exp, ExperimentAnalysis
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop, Wait


class T2Echo(ExperimentAnalysis, Exp):
    """Class used to run a T2Echo experiment on the given qubit. The experiment performs the following circuit:

    Drag(qubit, theta=np.pi / 2, phase=0)  # Equivalent to a pi/2 rotation arround the x axis
    Wait(qubit, t)                         # Wait for a variable amount of time
    Drag(qubit, theta=np.pi, phase=0)      # Equivalent to a pi rotation arround the x axis
    Wait(qubit, t)                         # Wait for a variable amount of time
    Drag(qubit, theta=np.pi / 2, phase=0)  # Equivalent to a pi/2 rotation arround the x axis
    Wait(qubit, t=measurement_buffer)      # Wait for a fixed ammount of time
    M(qubit)                               # Measurment of the qubit

    Args:
        platform (Platform): platform used to run the experiment.
        qubit (int): qubit index used in the experiment.
        wait_loop_values (ndarray): array of time values to wait for the `Wait` gates, the same value is used on both gates.
        repetition_duration: Default to 10000.
        measurement_buffer: Default to 100.
        hardware_average: number of averages performed by the hardware. Default to 10000.
    """

    def __init__(
        self,
        qubit: int,
        platform: Platform,
        wait_loop_values: np.ndarray,
        repetition_duration=10000,
        measurement_buffer=100,
        hardware_average=10000,
    ):
        self.wait_loop_values = wait_loop_values
        self.t2 = None
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

    def fit(self):
        def func_model(x, A, C, offset):
            return A * np.exp(-x / C) + offset

        model = Model(func_model)
        initval_A = np.mean(self.post_processed_results)
        initval_C = 15000

        model.set_param_hint("A", value=initval_A, vary=True)
        model.set_param_hint("C", value=initval_C, min=0, vary=True)
        model.set_param_hint("offset", value=0, vary=True)
        params = model.make_params()

        results = model.fit(data=self.post_processed_results, x=self.wait_loop_values, params=params)
        parameters = results.params.valuesdict()
        self.t2 = parameters["C"]
        return self.t2
