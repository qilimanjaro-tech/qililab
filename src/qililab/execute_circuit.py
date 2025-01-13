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

from typing import Any

from qibo.models import Circuit
from tqdm.auto import tqdm

from qililab.result import Result

from .data_management import build_platform


def execute(
    program: Circuit | list[Circuit],
    runcard: str | dict,
    nshots: int = 1,
    transpile_config: dict[str, Any] | None = None,
) -> Result | list[Result]:
    """Executes a Qibo circuit (or a list of circuits) with qililab and returns the results.

    The ``program`` argument is first translated into pulses using the transpilation settings of the runcard and the passed transpile
    configuration. Then the pulse will be compiled into the runcard machines assembly programs, and executed.

    The transpilation is performed using the :meth:`.CircuitTranspiler.transpile_circuit()` method. Refer to the method's documentation or :ref:`Transpilation <transpilation>` for more detailed information. The main stages of this process are:
    1. \\*)Routing, 2. \\**)Canceling Hermitian pairs, 3. Translate to native gates, 4. Commute virtual RZ & adding CZ phase corrections, 5. \\**)Optimize Drag gates, 6. Convert to pulse schedule.

    .. note ::

        \\*) `1.` is done only if ``routing=True`` is passed in ``transpile_config``. Otherwise its skipped.

        \\**) `2.` and `5.` are done only if ``optimize=True`` is passed in ``transpile_config``. Otherwise its skipped.

    Args:
        circuit (Circuit | list[Circuit]): Qibo Circuit.
        runcard (str | dict): If a string, path to the YAML file containing the serialization of the Platform to be
            used. If a dictionary, the serialized platform to be used.
        nshots (int, optional): Number of shots to execute. Defaults to 1.
        transpile_config (dict[str, Any], optional): Kwargs (``!circuit``) passed to the :meth:`.CircuitTranspiler.transpile_circuit()`
            method. Contains the configuration used during transpilation. Defaults to ``None`` (not changing any default value).
            Check the ``transpile_circuit()`` method documentation for the keys and values it can contain.

    Returns:
        Result | list[Result]: :class:`Result` class (or list of :class:`Result` classes) containing the results of the
            execution.

    |

    Example Usage:

    .. code-block:: python

        import numpy as np
        from qibo import Circuit, gates
        from qibo.transpiler import Sabre, ReverseTraversal
        import qililab as ql

        # Create circuit:
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

        # Create transpilation config:
        transpilation = {routing: True, optimize: False, router: Sabre, placer: ReverseTraversal}

        # Execute with automatic transpilation:
        probabilities = ql.execute(c, runcard="./runcards/galadriel.yml", transpile_config=transpilation)
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
                transpile_config=transpile_config,
            )
            for circuit in tqdm(program, total=len(program))
        ]
        platform.disconnect()
        return results[0] if len(results) == 1 else results
    except Exception as e:
        platform.disconnect()
        raise e
