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
from qibo.transpiler.placer import Placer
from qibo.transpiler.router import Router
from tqdm.auto import tqdm

from qililab.result import Result

from .data_management import build_platform


def execute(
    program: Circuit | list[Circuit],
    runcard: str | dict,
    nshots: int = 1,
    placer: Placer | type[Placer] | tuple[type[Placer], dict] | None = None,
    router: Router | type[Router] | tuple[type[Router], dict] | None = None,
    routing_iterations: int = 10,
    optimize: bool = True,
) -> Result | list[Result]:
    """Executes a Qibo circuit (or a list of circuits) with qililab and returns the results.

    The ``program`` argument is first translated into pulses using the transpilation settings of the runcard and the
    passed placer and router. Then the pulse will be compiled into the runcard machines assembly programs, and executed.

    The transpilation is performed using the :class:`CircuitTranspiler` and its ``transpile_circuits()`` method. Refer to the method's documentation for more detailed information. The main stages of this process are:

    1. Routing and Placement: Routes and places the circuit's logical qubits onto the chip's physical qubits. The final qubit layout is returned and logged. This step uses the `placer`, `router`, and `routing_iterations` parameters if provided; otherwise, default values are applied.
    2. Native Gate Translation: Translates the circuit into the chip's native gate set (CZ, RZ, Drag, Wait, and M (Measurement)).
    3. Pulse Schedule Conversion: Converts the native gate circuit into a pulse schedule using calibrated settings from the runcard.

    |

    If `optimize=True` (default behavior), the following optimizations are also performed:

    - Canceling adjacent pairs of Hermitian gates (H, X, Y, Z, CNOT, CZ, and SWAPs).
    - Applying virtual Z gates and phase corrections by combining multiple pulses into a single one and commuting them with virtual Z gates.

    Args:
        circuit (Circuit | list[Circuit]): Qibo Circuit.
        runcard (str | dict): If a string, path to the YAML file containing the serialization of the Platform to be
            used. If a dictionary, the serialized platform to be used.
        nshots (int, optional): Number of shots to execute. Defaults to 1.
        placer (Placer | type[Placer] | tuple[type[Placer], dict], optional): `Placer` instance, or subclass `type[Placer]` to
            use`, with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `ReverseTraversal`.
        router (Router | type[Router] | tuple[type[Router], dict], optional): `Router` instance, or subclass `type[Router]` to
            use,` with optionally, its kwargs dict (other than connectivity), both in a tuple. Defaults to `Sabre`.
        routing_iterations (int, optional): Number of times to repeat the routing pipeline, to keep the best stochastic result. Defaults to 10.
        optimize (bool, optional): whether to optimize the circuit and/or transpilation. Defaults to True.

    Returns:
        Result | list[Result]: :class:`Result` class (or list of :class:`Result` classes) containing the results of the
            execution.

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
        c.add(gates.CNOT(2, 0))
        c.add(gates.RY(4, np.pi / 4))
        c.add(gates.X(3))
        c.add(gates.M(*range(3)))
        c.add(gates.SWAP(4, 2))
        c.add(gates.RX(1, 3 * np.pi / 2))

        probabilities = ql.execute(c, runcard="./runcards/galadriel.yml")
    """
    if isinstance(program, Circuit):
        program = [program]

    # Initialize platform and connect to the instruments
    platform = build_platform(runcard=runcard)
    platform.connect()

    try:
        platform.initial_setup()
        platform.turn_on_instruments()
        results = [
            # Execute circuit
            platform.execute(
                circuit,
                num_avg=1,
                repetition_duration=200_000,
                num_bins=nshots,
                placer=placer,
                router=router,
                routing_iterations=routing_iterations,
                optimize=optimize,
            )
            for circuit in tqdm(program, total=len(program))
        ]
        platform.disconnect()
        return results[0] if len(results) == 1 else results
    except Exception as e:
        platform.disconnect()
        raise e
