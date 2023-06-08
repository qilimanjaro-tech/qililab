"""This file contains a pre-defined version of a Ramsey experiment."""
import numpy as np
from qibo.gates import RX, M
from qibo.models import Circuit

import qililab as ql
from qililab.experiment.portfolio import Exp, ExperimentAnalysis
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Wait


class Ramsey(ExperimentAnalysis, Exp):
    """Experiment to perform Ramsey measurement on a qubit.

    The Ramsey measurement is used to determine the coherence time of a qubit.
    It involves the following sequence of operations:
        1. Prepare the qubit in a superposition state by applying a π/2 pulse.
        2. Wait for a time t.
        3. Apply another π/2 pulse.
        4. Wait for a measurement buffer time.
        5. Measure the state of the qubit.

    Args:
        platform (Platform): platform used to run the experiment
        qubit (int): qubit index used in the experiment
        wait_loop_values (numpy.ndarray): array of values to loop through in the experiment, which modifies the t parameter of the Wait gate
        delta_artificial (float): artificial detuning.
        if_frequency_values (numpy.ndarray | None, optional): array of intermediate frequency to loop through in the experiment. Defaults to None.
        measurement_buffer (int, optional): measurement buffer time in nanoseconds. Defaults to 40.
        repetition_duration (int, optional): duration of a single repetition in nanoseconds. Defaults to 200000.
        hardware_average (int, optional): number of repetitions used to average the result. Defaults to 10000.
    """

    def __init__(
        self,
        qubit: int,
        platform: Platform,
        wait_loop_values: np.ndarray,
        delta_artificial: float,
        if_frequency_values: np.ndarray | None = None,
        measurement_buffer: int = 40,
        repetition_duration=10000,
        hardware_average=10000,
    ):
        self.if_frequency_values = if_frequency_values
        self.wait_loop_values = wait_loop_values

        # Define Circuit to execute
        circuit = Circuit(qubit + 1)
        circuit.add(ql.Drag(qubit, theta=np.pi / 2, phase=0))
        circuit.add(Wait(qubit, t=0))
        circuit.add(ql.Drag(qubit, theta=np.pi / 2, phase=0))
        circuit.add(Wait(qubit, t=measurement_buffer))
        circuit.add(M(qubit))

        wait_loop = ql.Loop(alias="2", parameter=Parameter.GATE_PARAMETER, values=wait_loop_values)
        phi_values = 2 * np.pi * delta_artificial * wait_loop_values
        phi_loop = ql.Loop(alias="4", parameter=Parameter.GATE_PARAMETER, values=phi_values)

        if if_frequency_values is not None:
            if_loop = ql.Loop(
                alias=f"drive_line_q{qubit}_bus",
                parameter=Parameter.LO_FREQUENCY,
                values=if_frequency_values,
                channel_id=0,
                loop=wait_loop,
            )
            dummy_loop = ql.Loop(
                alias="external", parameter=Parameter.EXTERNAL, values=if_frequency_values, loop=phi_loop
            )

        experiment_options = ExperimentOptions(
            name="ramsey",
            loops=[if_loop, dummy_loop] if if_frequency_values is not None else [wait_loop, phi_loop],
            settings=ExperimentSettings(repetition_duration=repetition_duration, hardware_average=hardware_average),
        )

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=[circuit],
            options=experiment_options,
        )

    def post_process_results(self):
        super().post_process_results()
        if self.if_frequency_values is not None:
            self.post_processed_results = self.post_processed_results.reshape(
                len(self.if_frequency_values), len(self.wait_loop_values)
            )
        return self.post_processed_results
