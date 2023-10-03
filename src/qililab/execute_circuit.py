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

"""Execute function used to execute a qibo Circuit using the given runcard."""
from qibo.models import Circuit

from .data_management import build_platform
from .transpiler import translate_circuit


def execute(program: Circuit | list[Circuit], runcard: str | dict, nshots: int = 1):
    """Execute a qibo with qililab and native gates

    Args:
        circuit (Circuit): Qibo Circuit.
        runcard (str | dict): If a string, path to the YAML file containing the serialization of the Platform to be
            used. If a dictionary, the serialized platform to be used.
        nshots (int, optional): Number of shots to execute. Defaults to 1.

    Returns:
        Results: ``Results`` class containing the experiment results

    Example Usage:

    .. code-block:: python

        from qibo.models import Circuit
        from qibo import gates
        from pathlib import Path
        import qililab as ql
        import os
        import numpy as np

        nqubits = 5
        c = Circuit(nqubits)
        for qubit in range(nqubits):
            c.add(gates.H(qubit))
        c.add(gates.CNOT(2,0))
        c.add(gates.RY(4,np.pi / 4))
        c.add(gates.X(3))
        c.add(gates.M(*range(3)))
        c.add(gates.SWAP(4,2))
        c.add(gates.RX(1, 3*np.pi/2))

        probabilities = ql.execute(c, runcard="./runcards/galadriel.yml")


    """
    if isinstance(program, Circuit):
        program = [program]

    # Initialize platform and connect to the instruments
    platform = build_platform(runcard=runcard)
    platform.connect()
    platform.initial_setup()
    platform.turn_on_instruments()

    try:
        results = []
        for circuit in program:
            # Transpile and optimize circuit
            program = translate_circuit(circuit, optimize=True)
            # Execute circuit
            results.append(platform.execute(circuit, num_avg=1, repetition_duration=200_000, num_bins=nshots))
        platform.disconnect()
        return results
    except Exception as e:
        platform.disconnect()
        raise e
