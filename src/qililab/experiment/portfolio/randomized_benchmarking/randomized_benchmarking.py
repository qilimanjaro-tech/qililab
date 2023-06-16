"""
File containing the RandomizedBenchmarking and CliffordGate classes
"""
import logging
import os
import pathlib

import lmfit as lm
import matplotlib.pyplot as plt
import numpy as np
import yaml
from qibo.gates import RX, RY, I, M
from qibo.models.circuit import Circuit

import qililab as ql
from qililab.platform import Platform
from qililab.typings import Parameter
from qililab.utils import Loop

NUM_CLIFFORD_GATES = 24

NG = 1.875  # average number of gates per Clifford


class CliffordGate:
    def __init__(self, idx: int, qubit_idx, num_qubits) -> None:
        """Class to multiply and inverd Clifford gates.

        Params:
            idx: (int) which Clifford gate
            qubit_idx: (int) which qubit the gate is applied to
            num_qubits: (int) total number of qubits in the system
        """
        if not (0 <= idx <= 23):
            logging.error("Index must be between 0 and 23")
        self.idx = idx
        self.qubit_idx = qubit_idx
        self.num_qubits = num_qubits

        # Read YAML file
        with open(pathlib.Path(__file__).parent / "cliffords.yaml", "r") as file:
            try:
                f = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                logging.error(exc)

        self.prim_gates = f["primitive_gates"]
        self.clifford_gates = f["clifford_gates"]
        self._gate = self.clifford_gates[idx]

        # Add qibo gates to prim_gates dictionary
        for gate_num in self.prim_gates:
            self.prim_gates[gate_num]["gate"] = self._get_primitive_gates(qubit_idx)[self.prim_gates[gate_num]["name"]]

        self.clifford_products = np.loadtxt(
            pathlib.Path(__file__).parent / "clifford_products.csv", delimiter=",", dtype=int
        )

        self.clifford_inverses = np.loadtxt(
            pathlib.Path(__file__).parent / "clifford_inverses.csv", delimiter=",", dtype=int
        )

    @property
    def inverse(self):
        """
        Returns the inverse as a CliffordGate object
        """
        return CliffordGate(self.clifford_inverses[self.idx], self.qubit_idx, self.num_qubits)

    @property
    def gate_decomp(self) -> list[str]:
        """
        Returns the decomposition of the Clifford gate into
        primitives gates.
        """
        return [self.prim_gates[gate]["name"] for gate in map(int, str(self._gate))]

    @property
    def matrix(self) -> np.ndarray:
        """
        Returns matrix representation of Clifford gate
        """
        u = np.identity(2)
        # Reverse order of matrices
        for gate in list(map(int, str(self._gate)))[::-1]:
            u = u @ self.prim_gates[gate]["gate"].matrix
        return u

    @property
    def circuit(self) -> Circuit:
        circuit = Circuit(self.num_qubits)
        for gate in list(map(int, str(self._gate))):
            circuit.add(self.prim_gates[gate]["gate"])

        return circuit

    def __mul__(self, right):
        """
        Overload of the left multiply operator: clifford_gate * right
        """
        if not isinstance(right, CliffordGate):
            logging.error("Using non CliffordGate object as multiplying factor")

        return CliffordGate(self.clifford_products[self.idx][right.idx], self.qubit_idx, self.num_qubits)

    def __rmul__(self, left):
        """
        Overload of the right multiply operator: left * clifford_gate
        """
        if not isinstance(left, CliffordGate):
            logging.error("Using non CliffordGate object as multiplying factor")

        return CliffordGate(self.clifford_products[left.idx][self.idx], self.qubit_idx, self.num_qubits)

    def __repr__(self):
        return f"C{self.idx} = {' * '.join(reversed(self.gate_decomp))}"

    def _get_primitive_gates(self, qubit_idx):
        """returns primitive gates for the clifford products

        Args:
            qubit_idx (int): qubit index

        Returns:
            dict[str: Gate]: name of the gate and gate
        """

        return {
            "I": I(qubit_idx),
            "X_pi/2": RX(qubit_idx, np.pi / 2),
            "Y_pi/2": RY(qubit_idx, np.pi / 2),
            "X_pi": RX(qubit_idx, np.pi),
            "Y_pi": RY(qubit_idx, np.pi),
        }


class RandomizedBenchmarking:
    def __init__(
        self,
        length_list: list[int],
        platform: Platform,
        num_seeds: int = 1,
        num_qubits: int = 5,
        qubit_idx: int = 1,
        seed: int = 70,
        simulation: bool = True,
        initial_fit_params_I: dict | None = None,
        initial_fit_params_X: dict | None = None,
    ) -> None:
        """
        Run randomized benchmarking experiment.

        Params:
            length_list: (list[int]) list of integers for how many Cliffords to apply in one circuit
            num_seeds: (int) number of random circuits to generate for each length
            num_qubits: (int) number of qubits in the system
            qubit_idx: (int) id of qubit where the measurment is applied
            seed: (int) seed for random number generator
            simulation: (bool) if True, the experiment runs on a qibo circuit and produces populations instead of I-values
            runcard_name: (str) name of runcard for setting of the lab
        """
        self.length_list = length_list  # list of number of gates used
        self.num_seeds = num_seeds  # number of seeds used per circuit
        self.seed = seed  # random seed
        self._circuits = []  # type: list[dict[str, list[Circuit]]]  # list of circuits
        self.simulation = simulation  # run simulation with qibo or real experiment with qililab
        self.loops = []  # type: list[np.ndarray] # TODO: this is only used in a child class
        self.num_qubits = num_qubits
        self.qubit_idx = qubit_idx
        self.signal = None  # type: dict[str, dict] | None
        self.platform = platform

        # initial fit parameters
        self.initial_fit_params_I = initial_fit_params_I
        self.initial_fit_params_X = initial_fit_params_X

    @property
    def seed(self) -> int:
        """
        Returns:
            int: Seed value
        """
        return self._seed

    @seed.setter
    def seed(self, value: int) -> None:
        """Sets the seed of the random number generator.

        Args:
            value (int): New seed
        """
        self._seed = value
        self.rng = np.random.default_rng(seed=self._seed)

    @property
    def circuits(self) -> list[dict[str, list[Circuit]]]:
        """Generate a sequence of gates for each value in self.length_list

        Returns:
            Tuple[list[dict], list[dict]]: lists of N=len(self.length_list) elements,
            where each element is a dictionary containing M=self.num_seeds sequences
            equivalent to the I gate, and M sequences equivalent to the X gate.
        """

        # TODO: Delete sequence_list
        circuit_list = []  # type: list[dict[str, list[Circuit]]]
        for n in self.length_list:
            circuits = self._generate_gate_sequences(n=n)
            circuit_list.append(circuits)

        self._circuits = circuit_list

        return self._circuits

    def run(self, options, nshots: int = 1024, get_experiment_only: bool = False) -> dict[str, dict]:
        """Runs the randomized benchmarking experiment.

        Returns:
            dict[int, float]: dictionary that includes the voltage amplitude or probability of being in the
            ground state for each number of Clifford gates applied.
        """

        circuits = self.circuits
        signal = {"I": {}, "X": {}}  # type: dict[str, dict]
        for n_gates, circuit_dict in zip(self.length_list, circuits):
            for gate in ["I", "X"]:
                avg_result = []
                for i in range(self.num_seeds):
                    circuit = circuit_dict[gate][i]

                    if self.simulation:
                        result = circuit.execute(nshots=nshots)
                        avg_result.append(result.probabilities()[0])
                    else:
                        result = self._execute_qibo_circuit(
                            circuit, options, get_experiment_only=get_experiment_only
                        )  # TODO add nshots?
                        if get_experiment_only:
                            avg_result.append(
                                result
                            )  # TODO this changes the returned type, or remove - only for debugging anyway
                            return result
                        else:
                            if len(self.loops) == 0:
                                acquisitions = result.results[
                                    0
                                ].acquisitions()  # TODO understand why result.results[0] and not result.axquisition()??
                                i = np.array(acquisitions["i"])
                                q = np.array(acquisitions["q"])
                                amp = 20 * np.log10(np.abs(i + 1j * q))
                                avg_result.append(amp)
                            # TODO: pretty sure this is never run (loops are used in RBWithLoops class below)
                            # also, results_shape is not defined anywhere
                            # else:
                            #     acquisitions = result.acquisitions()
                            #     i = np.array(acquisitions["i"]).reshape(self.results_shape)
                            #     q = np.array(acquisitions["q"]).reshape(self.results_shape)
                            #     amp = 20 * np.log10(np.abs(i + 1j * q))
                            #     avg_result.append(amp)
                signal[gate].update({n_gates: np.mean(np.array(avg_result), axis=0)})

        self.signal = signal
        return signal

    def _execute_qibo_circuit(self, circuit, options, get_experiment_only: bool = False):
        """Take a qibo circuit, turn it into qililab.Experiment and run it.

        Params:
            circuit: (qibo.models.circuit.Circuit) circuit to run
            get_experiment_only: (bool) if True, only generate Experiment object and return it without execution
        """

        # transpile and optimize circuit
        circuit = ql.translate_circuit(circuit, optimize=True)
        # TODO: weird that mypy complains but this has been run and worked
        # did we move circuit to ExperimentAnalysis or something?
        # pylint: disable = unexpected-keyword-arg
        sample_experiment = ql.Experiment(  # type: ignore
            platform=self.platform,  # platform to run the experiment
            circuits=[circuit],  # circuits to run the experiment
            options=options,  # experiment options
        )
        sample_experiment.build_execution()
        return sample_experiment.run()

    def _generate_gate_sequences(self, n: int) -> dict[str, list[Circuit]]:
        """Generates 2 groups of gate sequences that correspond to I and X, respectively.
        Each group will have N=self.num_seeds sequences, each with a different seed.

        Args:
            n (int): Number of Clifford gates

        Returns:
            dict[str, list[Circuit]]: dictionary containing sequences that correspond
            to I and X, respectively.
        """
        circuits = {"I": [], "X": []}  # type: dict[str, list]
        for _ in range(self.num_seeds):
            circuit = Circuit(self.num_qubits)
            unitary = CliffordGate(0, self.qubit_idx, self.num_qubits)  # identity
            for _ in range(n):
                random_idx = self.rng.integers(0, NUM_CLIFFORD_GATES)
                tmp_gate = CliffordGate(random_idx, self.qubit_idx, self.num_qubits)
                circuit += tmp_gate.circuit
                unitary = tmp_gate * unitary

            # add inverse to sequence
            circuit_I = circuit + unitary.inverse.circuit
            # add Clifford gate such that sequence is equivalent to X gate
            final_gate = CliffordGate(3, self.qubit_idx, self.num_qubits) * unitary.inverse  # CliffordGate(3) = X gate
            circuit_X = circuit + final_gate.circuit
            # add measurement gates
            circuit_I.add(M(self.qubit_idx))
            circuit_X.add(M(self.qubit_idx))
            # append to lists
            circuits["I"].append(circuit_I)
            circuits["X"].append(circuit_X)
            # Change seed
            self.seed += 1

        return circuits

    def plot_fit(
        self, initial_params_I: dict[str, float] | None = None, initial_params_X: dict[str, float] | None = None
    ):
        def expfunc(x, a, tau, offset):
            """exponential function to fit"""

            return offset + a * np.exp(-x / tau)

        if initial_params_I is None:
            initial_params_I = {"tau": 45, "A": 2, "offset": -44.5}
        if initial_params_X is None:
            initial_params_X = {"tau": 45, "A": -2, "offset": -44.5}

        # TODO: fit is over linear signal, not logs(db) so this is an approximation
        # analysis and results should run separately

        this_I = self.Id.flatten()  # type: ignore
        this_X = self.X.flatten()  # type: ignore
        fit_mod_I = lm.Model(expfunc)
        fit_mod_X = lm.Model(expfunc)

        fit_mod_I.set_param_hint("a", value=np.min(this_I) - np.max(this_I), vary=False)
        fit_mod_I.set_param_hint("offset", value=initial_params_I["offset"])
        fit_mod_I.set_param_hint("tau", value=initial_params_I["tau"], min=0)
        pars_I = fit_mod_I.make_params()

        fit_mod_X.set_param_hint("a", value=np.max(this_X) - np.min(this_X), vary=False)
        fit_mod_X.set_param_hint("offset", value=initial_params_X["offset"])
        fit_mod_X.set_param_hint("tau", value=initial_params_X["tau"], min=0)
        pars_X = fit_mod_X.make_params()

        fit_res_I = fit_mod_I.fit(data=this_I, x=self.length_list, params=pars_I)
        fit_res_X = fit_mod_X.fit(data=this_X, x=self.length_list, params=pars_X)

        gate_fid = np.exp(-1.0 / fit_res_I.best_values["tau"]) ** (1 / 1.875)
        gate_fid = (1 + gate_fid) / 2

        fig = plt.figure()
        plt.plot(self.length_list, this_I, "--*", label=r"$\langle signal I \rangle$")
        plt.plot(self.length_list, this_X, "--*", label=r"$\langle signal X \rangle$")
        plt.plot(self.length_list, fit_res_I.best_fit, c="red", label=r"$\langle signal I \rangle$ FIT")
        plt.plot(self.length_list, fit_res_X.best_fit, c="teal", label=r"$\langle signal X \rangle$ FIT")
        plt.xlabel("# Cliffords")
        plt.ylabel("Signal (a.u.)")
        plt.title(f"Gate Fidelity = {gate_fid:.4f}")

        return fig, fit_res_I, fit_res_X, gate_fid

    @property
    def length(self):
        this_length = sorted(self.signal["I"].items(), key=lambda item: item[0])
        return np.array([ll[0] for ll in this_length])

    @property
    def Id(self):
        i = sorted(self.signal["I"].items(), key=lambda item: item[0])
        return np.array([ii[1] for ii in i])

    @property
    def X(self):
        x = sorted(self.signal["X"].items(), key=lambda item: item[0])
        return np.array([xx[1] for xx in x])


class RandomizedBenchmarkingWithLoops(RandomizedBenchmarking):
    def __init__(
        self,
        length_list: list[int],
        platform,
        num_seeds: int = 1,
        num_qubits: int = 5,
        qubit_idx: int = 1,
        seed: int = 70,
        simulation: bool = True,
        runcard_name: str = "runcards/soprano_master_sauron",
        amplitude_values: np.ndarray | None = None,
        frequency_values: np.ndarray | None = None,
        drag_coeff_values: np.ndarray | None = None,
    ) -> None:
        """
        Run randomized benchmarking experiment with loops over pulse parameters.

        Params:
            length_list: (list[int]) list of integers for how many Cliffords to apply in one circuit
            num_seeds: (int) number of random circuits to generate for each length
            num_qubits: (int) number of qubits in the system
            qubit_idx: (int) id of qubit where the measurment is applied
            seed: (int) seed for random number generator
            simulation: (bool) if True, the experiment runs on a qibo circuit and produces populations instead of I-values
            runcard_name: (str) name of runcard for setting of the lab
            amplitude_values: (ndarray) list of amplitude values to loop over
            frequency_values: (ndarray) list of frequency values to loop over
            drag_coeff_values: (ndarray) list of drag coefficients values to loop over
        """
        super(RandomizedBenchmarkingWithLoops, self).__init__(
            length_list,
            platform,
            num_seeds=num_seeds,
            num_qubits=num_qubits,
            qubit_idx=qubit_idx,
            seed=seed,
            simulation=simulation,
        )
        self.amplitude_values = amplitude_values
        self.frequency_values = frequency_values
        self.drag_coeff_values = drag_coeff_values
        self.qubit_idx = qubit_idx

        qubit_sequencer_mapping = {0: 0, 1: 1, 2: 0, 3: 0, 4: 1}  # TODO what is this and why?
        sequencer = qubit_sequencer_mapping[qubit_idx]

        outer_loop = None
        self.results_shape = []  # type: list[int]
        if amplitude_values is not None:
            amplitude_loop = Loop(
                alias=f"Drag({self.qubit_idx})", parameter=Parameter.AMPLITUDE, values=amplitude_values
            )
            outer_loop = amplitude_loop
            self.results_shape.append(len(amplitude_values))
        else:
            amplitude_loop = None

        if frequency_values is not None:
            frequency_loop = Loop(
                alias=f"drive_line_q{self.qubit_idx}_bus",
                parameter=Parameter.IF,
                values=frequency_values,
                loop=amplitude_loop,
                channel_id=sequencer,
            )
            outer_loop = frequency_loop
            self.results_shape.append(len(frequency_values))
        else:
            frequency_loop = None

        if drag_coeff_values is not None:
            drag_coeff_loop = Loop(
                alias=f"Drag({self.qubit_idx})",
                parameter=Parameter.DRAG_COEFFICIENT,
                values=drag_coeff_values,
                loop=frequency_loop or amplitude_loop or None,
            )
            outer_loop = drag_coeff_loop
            self.results_shape.append(len(drag_coeff_values))
        else:
            drag_coeff_loop = None
        self.loops = [outer_loop]
        self.results_shape = tuple(self.results_shape[::-1])  # type: ignore

    def plot(
        self,
        length_idx: int = 0,
        x_axis: str = "amplitude",
        y_axis: str = "frequency",
    ):
        """plot the data over loop ranges.

        Params:
            length_idx: (int) which element of the lenght_list to use for plotting
            x_axis: (str) plot 'amplitude', 'frequency' or 'drag_coeff' on x-axis
            y_axis: (str) plot 'amplitude', 'frequency' or 'drag_coeff' on y-axis
        """
        mapper = {
            "amplitude": self.amplitude_values,
            "frequency": self.frequency_values,
            "drag_coeff": self.drag_coeff_values,
        }

        if x_axis not in mapper.keys() or y_axis not in mapper.keys():
            raise NotImplementedError("x_axis and y_axis need to be one of 'amplitude', 'frequency' or 'drag_coeff'")

        x = mapper[x_axis]
        y = mapper[y_axis]

        if x is None or y is None:
            raise ValueError(f"either {x_axis} or {y_axis} was not measured")

        # compute shape of data tensor
        shape = []
        if self.drag_coeff_values is not None:
            shape.append(len(self.drag_coeff_values))
        if self.frequency_values is not None:
            shape.append(len(self.frequency_values))
        if self.amplitude_values is not None:
            shape.append(len(self.amplitude_values))

        I_tensor = self.Id[length_idx].reshape(shape)

        # plot stuff
        Y, X = np.meshgrid(y, x)
        plt.pcolor(I_tensor.transpose())
        plt.xlabel(x_axis)
        plt.ylabel(y_axis)
        plt.title(f"I for # Cliffords: {self.length[length_idx]}")
        plt.colorbar()
        plt.show()
