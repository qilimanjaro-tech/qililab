# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import re

import numpy as np
from qilisdk.digital import CZ, Circuit, M

from qililab.core.variables import Domain
from qililab.qprogram import QProgram
from qililab.qprogram.operations import ResetPhase
from qililab.settings.digital import DigitalCompilationSettings, GateEvent
from qilisdk.qprogram.waveforms import Arbitrary, IQDrag, IQPair, Square, Waveform

from .native_gates import Rmw


def extract_qubit_index(s: str) -> int:
    match = re.search(r"q(\d+)", s)
    if not match:
        raise ValueError(f"No qubit index found in string: {s}")
    return int(match.group(1))


def angle_to_0_2pi(a: float) -> float:
    """Map angle from [-π, π] to [0, 2π]."""
    if a < 0:
        return a + 2 * np.pi
    return a


class CircuitToQProgramCompiler:
    def __init__(self, settings: DigitalCompilationSettings):
        self._settings = settings

    def compile(self, circuit: Circuit, nshots: int) -> QProgram:
        qp = QProgram()
        bin_variable = qp.variable(label="Bin", domain=Domain.Scalar, type=int)
        with qp.for_loop(bin_variable, start=0, stop=nshots - 1):
            for gate in circuit.gates:
                if isinstance(gate, Rmw):
                    gate_events = self._settings.get_gate(name=gate.name, qubits=gate.target_qubits[0])
                    related_qubits = {
                        *gate.qubits,
                        *(extract_qubit_index(gate_event.bus) for gate_event in gate_events),
                    }
                    buses_to_sync = [
                        f"{kind}_q{q}_bus" for q in related_qubits for kind in ("drive", "flux", "readout")
                    ]
                    qp.sync(buses_to_sync)
                    for gate_event in gate_events:
                        if isinstance(gate_event.waveform, IQDrag):
                            iqdrag, phase = CircuitToQProgramCompiler.iqdrag_and_phase_from_calibrated_pi_drag(
                                target_rmw=gate, calibrated_pi_drag=gate_event.waveform
                            )
                            qp.set_gain(bus=gate_event.bus, gain=iqdrag.amplitude)
                            qp.set_phase(bus=gate_event.bus, phase=angle_to_0_2pi(phase))
                            qp.play(
                                bus=gate_event.bus,
                                waveform=IQDrag(
                                    amplitude=1.0,
                                    duration=iqdrag.duration,
                                    num_sigmas=iqdrag.num_sigmas,
                                    drag_coefficient=iqdrag.drag_coefficient,
                                ),
                            )
                elif isinstance(gate, CZ):
                    gate_events = self._settings.get_gate(
                        name=gate.name, qubits=(gate.control_qubits[0], gate.target_qubits[0])
                    )
                    related_qubits = {
                        *gate.qubits,
                        *(extract_qubit_index(gate_event.bus) for gate_event in gate_events),
                    }
                    buses_to_sync = [
                        f"{kind}_q{q}_bus" for q in related_qubits for kind in ("drive", "flux", "readout")
                    ]
                    qp.sync(buses_to_sync)
                    for gate_event in gate_events:
                        if isinstance(gate_event.waveform, Square):
                            qp.set_gain(bus=gate_event.bus, gain=gate_event.waveform.amplitude)  # type: ignore
                            qp.play(
                                bus=gate_event.bus,
                                waveform=Square(amplitude=1.0, duration=gate_event.waveform.duration),
                            )
                    qp.sync(buses_to_sync)
                elif isinstance(gate, M):
                    qubit_gate_events: list[tuple[int, list[GateEvent]]] = []
                    related_qubits = set(gate.qubits)
                    for qubit in gate.qubits:
                        gate_events = self._settings.get_gate(name=gate.name, qubits=qubit)
                        qubit_gate_events.append((qubit, gate_events))
                        related_qubits.update(extract_qubit_index(gate_event.bus) for gate_event in gate_events)
                    buses_to_sync = [
                        f"{kind}_q{q}_bus" for q in related_qubits for kind in ("drive", "flux", "readout")
                    ]
                    qp.sync(buses_to_sync)
                    for qubit, gate_events in qubit_gate_events:
                        for gate_event in gate_events:
                            if gate_event.weights is None:
                                raise ValueError(f"M({qubit}) does not have weights defined.")
                            if isinstance(gate_event.waveform, Waveform):
                                qp.measure(
                                    bus=gate_event.bus,
                                    waveform=IQPair(
                                        I=gate_event.waveform,
                                        Q=Square(amplitude=0.0, duration=gate_event.waveform.get_duration()),
                                    ),
                                    weights=gate_event.weights,
                                )
                            else:
                                qp.measure(bus=gate_event.bus, waveform=gate_event.waveform, weights=gate_event.weights)
                            qp.wait(bus=gate_event.bus, duration=self._settings.relaxation_duration)

        # Hacky way to add reset phases
        all_fluxes = {f"flux_q{q}_bus" for q in range(circuit.nqubits)}
        for bus in qp.buses | all_fluxes:
            qp._buses.add(bus)
            qp.body.elements.insert(0, ResetPhase(bus))

        return qp

    @staticmethod
    def wrap_to_pi(x: float) -> float:
        return (x + np.pi) % (2.0 * np.pi) - np.pi

    @staticmethod
    def iqdrag_and_phase_from_calibrated_pi_drag(target_rmw: Rmw, calibrated_pi_drag: IQDrag) -> tuple[IQDrag, float]:
        """
        Build (I, Q) envelopes for a microwave rotation Rmw(theta, phase),
        starting from a DRAG waveform calibrated for an X (π) rotation.

        Args:
            drag: IQDrag with parameters (amplitude, duration, num_sigmas, drag_coefficient)
                    calibrated to produce a π rotation about +X when phase=0.
            theta: desired rotation angle in radians.
            phase: rotation axis phase in radians (0 -> X, +π/2 -> Y).

        Returns:
            I_env, Q_env: numpy arrays for the rotated-and-scaled envelopes.
        """
        theta = CircuitToQProgramCompiler.wrap_to_pi(target_rmw.theta)
        amplitude = calibrated_pi_drag.amplitude * theta / np.pi

        phase = CircuitToQProgramCompiler.wrap_to_pi(target_rmw.phase)

        if amplitude < 0:
            amplitude = -amplitude
            phase = CircuitToQProgramCompiler.wrap_to_pi(target_rmw.phase + np.pi)

        return IQDrag(
            amplitude=amplitude,
            duration=calibrated_pi_drag.duration,
            num_sigmas=calibrated_pi_drag.num_sigmas,
            drag_coefficient=calibrated_pi_drag.drag_coefficient,
        ), phase

    @staticmethod
    def _rmw_from_calibrated_pi_drag(pi_drag: IQDrag, theta: float, phase: float) -> IQPair:
        """
        Build (I, Q) envelopes for a microwave rotation Rmw(theta, phase),
        starting from a DRAG waveform calibrated for an X (π) rotation.

        Args:
            drag: IQDrag with parameters (amplitude, duration, num_sigmas, drag_coefficient)
                    calibrated to produce a π rotation about +X when phase=0.
            theta: desired rotation angle in radians.
            phase: rotation axis phase in radians (0 -> X, +π/2 -> Y).

        Returns:
            I_env, Q_env: numpy arrays for the rotated-and-scaled envelopes.
        """
        theta_mod = CircuitToQProgramCompiler.wrap_to_pi(theta)

        # Push negative theta into a +π phase shift
        if theta_mod < 0:
            theta_mod = -theta_mod
            phase += np.pi

        phase = CircuitToQProgramCompiler.wrap_to_pi(phase)

        I0 = pi_drag.get_I().envelope()
        Q0 = pi_drag.get_Q().envelope()

        c, s = np.cos(phase), np.sin(phase)
        scale = theta_mod / np.pi  # drag is a π-pulse; scale linearly to θ

        # Phase rotation in the IQ plane followed by θ scaling
        I_env = scale * (I0 * c - Q0 * s)
        Q_env = scale * (I0 * s + Q0 * c)

        return IQPair(Arbitrary(I_env), Arbitrary(Q_env))
