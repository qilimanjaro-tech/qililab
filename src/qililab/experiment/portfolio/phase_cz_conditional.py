# renamed to phase_cz_conditional to avoid circular imports from experiment_analysis at __init__


"""This file contains a pre-defined version of the chevron experiment."""
from abc import abstractmethod
from dataclasses import dataclass

import lmfit
import matplotlib.pyplot as plt
import numpy as np
from qibo.gates import CZ, M
from qibo.models import Circuit

import qililab as ql
from qililab.experiment.portfolio import Exp, ExperimentAnalysis
from qililab.platform import Platform
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.utils import Loop, Wait


class CzConditional(ExperimentAnalysis, Exp):
    def __init__(
        self,
        control_qubit: int,
        target_qubit: int,
        platform: Platform,
        phase_loop_values: np.ndarray,
        duration_loop_values: np.ndarray | None = None,
        amplitude_loop_values: np.ndarray | None = None,
        b_cz_loop_values: np.ndarray | None = None,
        park_qubit_id: int | None = None,
        experiment_gate: str = "Park",
        repetition_duration=10000,
        hardware_average=10000,
    ):
        self.control_qubit = control_qubit
        self.target_qubit = target_qubit
        self.phase_loop_values = phase_loop_values
        self.duration_loop_values = duration_loop_values
        self.amplitude_loop_values = amplitude_loop_values
        self.b_cz_loop_values = b_cz_loop_values
        self.platform = platform
        self.park_qubit_id = park_qubit_id
        self.nqubits = max(control_qubit, target_qubit) + 1
        self.experiment_gate = experiment_gate

        control_qubit_node_freq = self.platform.chip.get_node_from_qubit_idx(idx=control_qubit, readout=False).frequency
        target_qubit_node_freq = self.platform.chip.get_node_from_qubit_idx(idx=target_qubit, readout=False).frequency

        self.flux_active_qubit = control_qubit if control_qubit_node_freq > target_qubit_node_freq else target_qubit
        self.flux_passive_qubit = target_qubit if control_qubit_node_freq > target_qubit_node_freq else control_qubit

        self.drag_time = platform.settings.get_gate("Drag", self.flux_active_qubit).duration

        if self.experiment_gate == "Park":
            loop = self.park_experiment_loop()
        elif self.experiment_gate == "CZ":
            loop = self.cz_experiment_loop()
        else:
            raise ValueError(
                f"Experiment not supported for 2 qubit gate {self.experiment_gate}. Supported gates are Park and CZ"
            )

        c_off, c_on = self.get_off_on_c(control_qubit=self.control_qubit, target_qubit=self.target_qubit)

        experiment_options = ExperimentOptions(
            name="CZ_conditional",
            loops=loop,
            settings=ExperimentSettings(
                repetition_duration=repetition_duration,
                hardware_average=hardware_average,
            ),
        )

        super().__init__(
            platform=platform,
            circuits=[c_on, c_off],
            options=experiment_options,
        )

    def get_off_on_c(self, control_qubit: int, target_qubit: int):
        # sourcery skip: extract-duplicate-method
        """Returns off and on circuits from ramiro's jam

        Args:
            control_qubit (int): index of the control qubit
            target_qubit (int): index of the target qubit
        Returns:
            Circuit, Circuit: circuits for cz tuneup
        """
        theta_off = 0
        c_off = Circuit(self.nqubits)

        theta_on = np.pi
        c_on = Circuit(self.nqubits)

        # C_OFF CIRCUIT
        c_off.add(ql.Drag(control_qubit, theta=theta_off, phase=0))  # control qubit on 0
        c_off.add(ql.Drag(target_qubit, theta=np.pi / 2, phase=0))  # target qubit on |-i>
        if self.park_qubit_id is not None:
            c_off.add(Wait(self.park_qubit_id, t=self.drag_time))

        if self.experiment_gate == "Park":
            c_off.add(ql.Park(q=self.flux_active_qubit))
            c_off.add(Wait(self.flux_passive_qubit, t=self.square_time))
            if self.park_qubit_id is not None:
                c_off.add(ql.Park(self.park_qubit_id))
        elif self.experiment_gate == "CZ":
            c_off.add(CZ(self.flux_active_qubit, self.flux_passive_qubit))

        c_off.add(ql.Drag(control_qubit, theta=theta_off, phase=0))
        c_off.add(ql.Drag(target_qubit, theta=np.pi / 2, phase=0))  # target goes to |1>
        if self.park_qubit_id is not None:
            c_off.add(Wait(self.park_qubit_id, t=self.drag_time))

        c_off.add(M(control_qubit))
        c_off.add(M(target_qubit))

        # C_ON CIRCUIT
        c_on.add(ql.Drag(control_qubit, theta=theta_on, phase=0))  # control qubit on 0
        c_on.add(ql.Drag(target_qubit, theta=np.pi / 2, phase=0))  # target qubit on |-i>
        if self.park_qubit_id is not None:
            c_on.add(Wait(self.park_qubit_id, t=self.drag_time))

        if self.experiment_gate == "Park":
            c_on.add(ql.Park(q=self.flux_active_qubit))
            c_on.add(Wait(self.flux_passive_qubit, t=self.square_time))
            if self.park_qubit_id is not None:
                c_on.add(ql.Park(self.park_qubit_id))
        elif self.experiment_gate == "CZ":
            c_on.add(CZ(self.flux_active_qubit, self.flux_passive_qubit))

        c_on.add(ql.Drag(control_qubit, theta=theta_on, phase=0))
        c_on.add(ql.Drag(target_qubit, theta=np.pi / 2, phase=0))  # target goes to |0>
        if self.park_qubit_id is not None:
            c_on.add(Wait(self.park_qubit_id, t=self.drag_time))

        c_on.add(M(control_qubit))
        c_on.add(M(target_qubit))

        return c_on, c_off

    def post_process_results(self, snz_cal: bool = False):
        super().post_process_results()
        self.calc_dimensions(snz_cal)
        self.post_processed_results = self.post_processed_results.reshape(self.this_shape)
        return self.post_processed_results

    def calc_dimensions(self, snz_cal: bool = False):
        # it is not that we intend to generalize this to N qubits or M circuits
        # but rather that I like to explicit the meaning of dimensions when handling so many of them
        if snz_cal:
            loop = self.b_cz_loop_values
            loop_name = "B_cz"
        else:
            loop = self.duration_loop_values
            loop_name = "Duration"

        num_circuits = 2
        num_qubits = 2
        if self.amplitude_loop_values is not None:
            if loop is not None:
                self.this_shape = (
                    len(loop),
                    len(self.amplitude_loop_values),
                    num_circuits,
                    len(self.phase_loop_values),
                    num_qubits,
                )
                self.these_loops = {
                    "values": [self.amplitude_loop_values, loop],
                    "labels": [loop_name, "Amplitude"],
                }
            else:
                self.this_shape = (  # type: ignore
                    len(self.amplitude_loop_values),
                    num_circuits,
                    len(self.phase_loop_values),
                    num_qubits,
                )
                self.these_loops = {
                    "values": [self.amplitude_loop_values],
                    "labels": ["Amplitude"],
                }
        elif loop is not None:
            self.this_shape = (  # type: ignore
                len(loop),
                num_circuits,
                len(self.phase_loop_values),
                num_qubits,
            )
            self.these_loops = {
                "values": [loop],
                "labels": [loop_name],
            }
        else:
            self.this_shape = (num_circuits, len(self.phase_loop_values), num_qubits)  # type: ignore

    # def fit_all_curves(self):
    #     idx_target = 1 if self.target_qubit > self.control_qubit else 0

    #     if len(self.this_shape) == 3:  # dont have any loops
    #         self.fit_cosines(
    #             self.post_processed_results[:, :, idx_target], label="CondOsc"
    #         )
    #     elif len(self.this_shape) == 4:  # have one loop
    #         phase_diff_vec = []
    #         phase_offset_vec = []
    #         for iv, this_val in enumerate(self.these_loops["values"][0]):
    #             this_phase_diff, this_phase_offset = self.fit_cosines(
    #                 self.post_processed_results[iv, :, :, idx_target],
    #                 label=f"CondOsc_amp={this_val:.3f}",
    #             )
    #             phase_diff_vec.append(this_phase_diff)
    #             phase_offset_vec.append(this_phase_offset)
    #         self.generate_1d_plots(phase_diff_vec, phase_offset_vec)
    #     # TODO: did we ever run this with 2 loops??
    #     # this_phase_diff is a scalar (i think) so
    #     # phase_diff_matrix[-1].extend(this_phase_diff) does not work
    #     # also I havent seen any 2d plots for cz_conditional
    #     elif len(self.this_shape) == 5:  # have two loops
    #         phase_diff_matrix = []
    #         phase_offset_matrix = []
    #         for iv2, this_val_1 in enumerate(self.these_loops["values"][1]):
    #             phase_diff_matrix.append([])
    #             phase_offset_matrix.append([])
    #             for iv, this_val_2 in enumerate(self.these_loops["values"][0]):
    #                 this_phase_diff, this_phase_offset = self.fit_cosines(
    #                     self.post_processed_results[iv2, iv, :, :, idx_target],
    #                     label="CondOsc_duration={this_val_1:.3f}_amp={this_val_2:.3f}",
    #                 )
    #                 phase_diff_matrix[-1].extend(this_phase_diff)
    #                 phase_offset_matrix[-1].extend(this_phase_offset)
    #         self.generate_2d_plots(phase_diff_matrix, phase_offset_matrix)

    def fit_cosines(self, cosines, label):
        def cosfunc(phi, A, omega, offset, phase_offset):
            return offset + A * np.cos(omega * phi + phase_offset)

        trace_off = cosines[0, :]
        trace_on = cosines[1, :]
        fit_mod_off = lmfit.Model(cosfunc)
        fit_mod_on = lmfit.Model(cosfunc)

        fit_mod_off.set_param_hint("A", value=(np.max(trace_off) - np.min(trace_off)) / 2, min=0)
        fit_mod_off.set_param_hint("omega", value=1, min=0, vary=False)
        fit_mod_off.set_param_hint("phase_offset", value=0, min=-np.pi, max=np.pi)
        fit_mod_off.set_param_hint("offset", value=np.mean(trace_off))
        pars_off = fit_mod_off.make_params()

        fit_mod_on.set_param_hint("A", value=(np.max(trace_on) - np.min(trace_on)) / 2, min=0)
        fit_mod_on.set_param_hint("omega", value=1, min=0, vary=False)
        fit_mod_on.set_param_hint("phase_offset", value=0, min=-np.pi, max=np.pi)
        fit_mod_on.set_param_hint("offset", value=np.mean(trace_on))
        pars_on = fit_mod_on.make_params()

        fit_res_off = fit_mod_off.fit(phi=self.phase_loop_values, data=trace_off, params=pars_off)
        fit_res_on = fit_mod_on.fit(phi=self.phase_loop_values, data=trace_on, params=pars_on)

        phase_diff = fit_res_on.best_values["phase_offset"] - fit_res_off.best_values["phase_offset"]
        phase_diff_deg = phase_diff * 180 / np.pi
        phase_dif_str = f"$\delta\phi =$ {phase_diff:2f} rad/ {phase_diff_deg:.1f}deg"

        fig, ax = plt.subplots()
        ax.plot(self.phase_loop_values, trace_off, "o", color="C0")
        ax.plot(self.phase_loop_values, trace_on, "o", color="C1")
        ax.plot(self.phase_loop_values, fit_res_off.best_fit, "-", color="C0")
        ax.plot(self.phase_loop_values, fit_res_on.best_fit, "-", color="C1")
        ax.set_title(f"{label}|{phase_dif_str}")
        ax.set_xlabel("Phase (rad)")
        ax.set_ylabel("|S21| (dB)")

        return phase_diff, fit_res_on.best_values["phase_offset"]

    # def generate_1d_plots(self, phase_diff_vec, phase_offset_vec):
    #     fig, axs = plt.subplots(2, 1, sharex=True)
    #     axs[0].plot(
    #         self.these_loops["values"][0], 180 * np.array(phase_diff_vec) / np.pi, "-o"
    #     )
    #     axs[1].plot(
    #         self.these_loops["values"][0],
    #         180 * np.array(phase_offset_vec) / np.pi,
    #         "-o",
    #     )
    #     axs[1].set_xlabel(self.these_loops["labels"][0])
    #     axs[0].set_ylabel("Phase difference $\delta\phi$ (rad)")
    #     axs[1].set_ylabel("Offset $\delta\phi_0$ (rad)")
    #     plt.show()

    # TODO: was this ever used (see TODO above)
    # def generate_2d_plots(self, phase_diff_matrix, phase_offset_matrix):
    #     fig, ax = plt.subplots()
    #     im = ax.pcolormesh(
    #         self.these_loops["values"][0],
    #         self.these_loops["values"][1],
    #         (180 / np.pi) * np.array(phase_diff_matrix),
    #         cmap="coolwarm",
    #         vmin=0,
    #         vmax=360,
    #     )
    #     ax.set_xlabel(self.these_loops["labels"][1])
    #     ax.set_ylabel(self.these_loops["labels"][0])
    #     ax.set_title(r"Phase difference")
    #     plt.colorbar(im, label=r"$\delta\phi$ (deg)")
    #     plt.show()
    #     fig, ax = plt.subplots()
    #     im = ax.pcolormesh(
    #         self.these_loops["values"][0],
    #         self.these_loops["values"][1],
    #         (180 / np.pi) * np.array(phase_offset_matrix),
    #         cmap="coolwarm",
    #     )
    #     ax.set_xlabel(self.these_loops["labels"][1])
    #     ax.set_ylabel(self.these_loops["labels"][0])
    #     ax.set_title(r"Offset")
    #     plt.colorbar(im, label=r"$\delta\phi_0$ (deg)")
    #     plt.show()

    def park_experiment_loop(self):
        """Returns loops for cz conditional using park gates

        Returns:
            Loop | list(Loop)
        """

        self.square_time = self.platform.settings.get_gate("Park", self.flux_active_qubit).duration

        phase_alias = "12" if self.park_qubit_id is not None else "10"
        phase_loop = Loop(alias=phase_alias, parameter=Parameter.GATE_PARAMETER, values=self.phase_loop_values)
        outer_loop = [phase_loop]

        if self.amplitude_loop_values is not None:
            amplitude_loop = Loop(
                alias=f"Park({self.flux_active_qubit})",
                parameter=Parameter.AMPLITUDE,
                values=self.amplitude_loop_values,
                loop=phase_loop,
            )
            outer_loop = [amplitude_loop]

        if self.duration_loop_values is not None:
            inner_loop = amplitude_loop if self.amplitude_loop_values is not None else phase_loop
            duration_loop_1 = Loop(
                alias=f"Park({self.flux_active_qubit})",
                parameter=Parameter.DURATION,
                values=self.duration_loop_values,
                loop=inner_loop,
            )
            t_wait_alias = "5" if self.park_qubit_id is not None else "4"
            duration_loop_2 = Loop(
                alias=t_wait_alias,
                parameter=Parameter.GATE_PARAMETER,
                values=self.duration_loop_values,
                loop=inner_loop,
            )
            outer_loop = [duration_loop_1, duration_loop_2]

        return outer_loop

    def cz_experiment_loop(self):
        """Cz conditional experiment using Cz gates.
        If b_cz_loop_values is defined then the experiment will loop over b_cz values
        INSTEAD of looping through gate duration.

        Returns:
            Loop | list(Loop) : loops for cz conditional using cz gates
        """

        phase_alias = "11" if self.park_qubit_id is not None else "9"

        phase_loop = Loop(alias=phase_alias, parameter=Parameter.GATE_PARAMETER, values=self.phase_loop_values)
        outer_loop = phase_loop

        if self.amplitude_loop_values is not None:
            amplitude_loop = Loop(
                alias=f"CZ({self.control_qubit},{self.target_qubit})",
                parameter=Parameter.AMPLITUDE,
                values=self.amplitude_loop_values,
                loop=phase_loop,
            )
            outer_loop = amplitude_loop

        if self.b_cz_loop_values is not None:
            inner_loop = phase_loop if self.amplitude_loop_values is None else amplitude_loop
            b_cz_loop = Loop(
                alias=f"CZ({self.flux_passive_qubit},{self.flux_active_qubit})",
                parameter=Parameter.B_CZ,
                values=self.b_cz_loop_values,
                loop=inner_loop,
            )

            outer_loop = b_cz_loop
        elif self.duration_loop_values is not None:
            inner_loop = phase_loop if self.amplitude_loop_values is None else amplitude_loop
            duration_loop = Loop(
                alias=f"CZ({self.flux_passive_qubit},{self.flux_active_qubit})",
                parameter=Parameter.DURATION,
                values=self.duration_loop_values,
                loop=inner_loop,
            )
            outer_loop = duration_loop
        else:
            raise ValueError("CZ conditional needs to have specified at least a duration or a b_cz loop")

        return outer_loop
