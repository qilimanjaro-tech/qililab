"""This file contains a pre-defined version of an AllXY experiment."""
from inspect import Parameter

import matplotlib.pyplot as plt
import numpy as np
from qibo.gates import M
from qibo.models import Circuit

import qililab as ql
from qililab import Drag
from qililab.experiment.portfolio import Cos, ExperimentAnalysis
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings
from qililab.utils import Wait
from qililab.utils.loop import Loop

class AllXYExperiment(ExperimentAnalysis, Cos):

    def __init__(
        self,
        platform: Platform,
        qubit: int,
        repetition_duration=10000,
        measurement_buffer=100,
        hardware_average=10000,
        if_values: np.ndarray | None = None,
    ):
        self.qubit = qubit
        self.gates = {
            "I": Drag(q=self.qubit, theta=np.pi, phase=0),
            "Xp": Drag(q=self.qubit, theta=np.pi, phase=0),
            "Yp": Drag(q=self.qubit, theta=np.pi, phase=np.pi/2),
            "X9": Drag(q=self.qubit, theta=np.pi/2, phase=0),
            "Y9": Drag(q=self.qubit, theta=np.pi/2, phase=np.pi/2),
            "Wait": Wait(self.qubit, t=measurement_buffer),
            "M": M(self.qubit)
        }
        
        self.circuits, self.circuit_names = self.get_circuits(qubits=self.qubit+1, gates=self.gates)
        self.num_experiments = 21
        self.if_values = if_values
        qubit_sequencer_mw_mapping = {0: 0, 1: 1, 2: 0, 3: 0, 4: 1}
        sequencer_mw = qubit_sequencer_mw_mapping[qubit]
    
        if if_values is not None:
            if_loop = Loop(alias=f'drive_line_q{qubit}_bus', parameter=ql.Parameter.IF,
                       channel_id=sequencer_mw, values=if_values.astype(list))

        _, control_bus, readout_bus = platform.get_bus_by_qubit_index(qubit)

        experiment_options = ExperimentOptions(
            name="AllXY Sequence",
            loops=None if if_values is not None else [if_loop],
            settings=ExperimentSettings(repetition_duration=repetition_duration,
                                        hardware_average=hardware_average)
            )
        loop = ql.Loop(alias="Sequence", parameter=ql.Parameter.A, values=self.circuit_names)

        # Initialize experiment
        super().__init__(
            platform=platform,
            circuits=self.circuits,
            options=experiment_options,
            control_bus=control_bus,
            readout_bus=readout_bus,
            experiment_loop=loop
        )

    def get_circuits(self, qubits:int, gates:dict):
        # II circuit
        circuit_ii = Circuit(qubits)
        circuit_ii.add(gates["I"])
        circuit_ii.add(gates["I"])

        # XpXp circuit
        circuit_xpxp = Circuit(qubits)
        circuit_xpxp.add(gates["Xp"])
        circuit_xpxp.add(gates["Xp"])

        # YpYp circuit
        circuit_ypyp = Circuit(qubits)
        circuit_ypyp.add(gates["Yp"])
        circuit_ypyp.add(gates["Yp"])

        # XpYp circuit
        circuit_xpyp = Circuit(qubits)
        circuit_xpyp.add(gates["Xp"])
        circuit_xpyp.add(gates["Yp"])

        # YpXp circuit
        circuit_ypxp = Circuit(qubits)
        circuit_ypxp.add(gates["Yp"])
        circuit_ypxp.add(gates["Xp"])

        # X9I circuit
        circuit_x9i = Circuit(qubits)
        circuit_x9i.add(gates["X9"])
        circuit_x9i.add(gates["I"])

        # Y9I circuit
        circuit_y9i = Circuit(qubits)
        circuit_y9i.add(gates["Y9"])
        circuit_y9i.add(gates["I"])

        # X9Y9 circuit
        circuit_x9y9 = Circuit(qubits)
        circuit_x9y9.add(gates["X9"])
        circuit_x9y9.add(gates["Y9"])

        # Y9X9 circuit
        circuit_y9x9 = Circuit(qubits)
        circuit_y9x9.add(gates["Y9"])
        circuit_y9x9.add(gates["X9"])

        # X9Yp circuit
        circuit_x9yp = Circuit(qubits)
        circuit_x9yp.add(gates["X9"])
        circuit_x9yp.add(gates["Yp"])

        # Y9Xp circuit
        circuit_y9xp = Circuit(qubits)
        circuit_y9xp.add(gates["Y9"])
        circuit_y9xp.add(gates["Xp"])

        # XpY9 circuit
        circuit_xpy9 = Circuit(qubits)
        circuit_xpy9.add(gates["Xp"])
        circuit_xpy9.add(gates["Y9"])

        # YpX9 circuit
        circuit_ypx9 = Circuit(qubits)
        circuit_ypx9.add(gates["Yp"])
        circuit_ypx9.add(gates["X9"])

        # X9Xp circuit
        circuit_x9xp = Circuit(qubits)
        circuit_x9xp.add(gates["X9"])
        circuit_x9xp.add(gates["Xp"])

        # XpX9 circuit
        circuit_xpx9 = Circuit(qubits)
        circuit_xpx9.add(gates["Xp"])
        circuit_xpx9.add(gates["X9"])

        # Y9Yp circuit
        circuit_y9yp = Circuit(qubits)
        circuit_y9yp.add(gates["Y9"])
        circuit_y9yp.add(gates["Yp"])

        # YpY9 circuit
        circuit_ypy9 = Circuit(qubits)
        circuit_ypy9.add(gates["Yp"])
        circuit_ypy9.add(gates["Y9"])

        # XpI circuit
        circuit_xpi = Circuit(qubits)
        circuit_xpi.add(gates["Xp"])
        circuit_xpi.add(gates["I"])

        # YpI circuit
        circuit_xpi = Circuit(qubits)
        circuit_xpi.add(gates["Yp"])
        circuit_xpi.add(gates["I"])

        # X9X9 circuit
        circuit_x9x9 = Circuit(qubits)
        circuit_x9x9.add(gates["X9"])
        circuit_x9x9.add(gates["X9"])

        # Y9Y9 circuit
        circuit_y9y9 = Circuit(qubits)
        circuit_y9y9.add(gates["Y9"])
        circuit_y9y9.add(gates["Y9"])

        circuits_names = ["II", "XpXp", "YpYp",
                          "XpYp", "YpXp", "X9I",
                          "Y9I", "X9Y9", "Y9X9",
                          "X9Yp", "Y9Xp", "XpY9",
                          "YpX9", "X9Xp", "XpX9",
                          "Y9Yp", "YpY9", "XpI",
                          "YpI", "X9X9", "Y9Y9"]

        circuits = [circuit_ii, circuit_xpxp, circuit_ypyp,
                    circuit_xpyp, circuit_ypxp, circuit_x9i,
                    circuit_y9i, circuit_x9y9, circuit_y9x9,
                    circuit_x9yp, circuit_y9xp, circuit_xpy9,
                    circuit_ypx9, circuit_x9xp, circuit_xpx9,
                    circuit_y9yp, circuit_ypy9, circuit_xpi,
                    circuit_xpi, circuit_x9x9, circuit_y9y9]

        # adding buffer waiting + measurement to all circuits
        for circuit in circuits:
            circuit.add(gates["Wait"])
            circuit.add(gates["M"])

        return circuits, circuits_names

    def post_process_results(self):
        super().post_process_results()
        if self.if_values is not None:
            self.post_processed_results = self.post_processed_results.reshape(
                len(self.if_values), 21
            )
        return self.post_processed_results
