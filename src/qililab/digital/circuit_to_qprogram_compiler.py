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
from qililab.settings.digital import DigitalCompilationSettings
from qililab.waveforms import IQDrag, IQPair, Square, Waveform, transform_pi_calibrated_waveform

from .native_gates import Rmw


def extract_qubit_index(s: str) -> int:
    match = re.search(r"q(\d+)", s)
    if not match:
        raise ValueError(f"No qubit index found in string: {s}")
    return int(match.group(1))


class CircuitToQProgramCompiler:
    def __init__(self, settings: DigitalCompilationSettings):
        self._settings = settings

    def compile(self, circuit: Circuit, nshots: int) -> QProgram:
        qp = QProgram()
        bin = qp.variable(label="Bin", domain=Domain.Scalar, type=int)
        with qp.for_loop(bin, start=0, stop=nshots - 1):
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
                            rmw = transform_pi_calibrated_waveform(
                                gate_event.waveform, gate.theta, gate.phase
                            )
                            qp.play(bus=gate_event.bus, waveform=rmw)
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
                        qp.play(bus=gate_event.bus, waveform=gate_event.waveform)
                elif isinstance(gate, M):
                    for qubit in gate.qubits:
                        gate_events = self._settings.get_gate(name=gate.name, qubits=qubit)
                        related_qubits = {
                            *gate.qubits,
                            *(extract_qubit_index(gate_event.bus) for gate_event in gate_events),
                        }
                        buses_to_sync = [
                            f"{kind}_q{q}_bus" for q in related_qubits for kind in ("drive", "flux", "readout")
                        ]
                        qp.sync(buses_to_sync)
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

        return qp

    @staticmethod
    def wrap_to_pi(x):
        return (x + np.pi) % (2 * np.pi) - np.pi
