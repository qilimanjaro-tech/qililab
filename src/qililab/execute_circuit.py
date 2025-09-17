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
from tqdm.auto import tqdm

from qililab.digital import DigitalTranspilationConfig
from qililab.result import Result

from .data_management import build_platform


def execute(
    program: Circuit | list[Circuit],
    runcard: str | dict,
    nshots: int = 1,
    transpilation_config: DigitalTranspilationConfig | None = None,
) -> Result | list[Result]:
    """Executes a Qibo circuit (or a list of circuits) with qililab and returns the results.

    The ``program`` argument is first translated into pulses using the transpilation settings of the runcard and the passed transpile
    configuration. Then the pulse will be compiled into the runcard machines assembly programs, and executed.

    The transpilation is performed using the :meth:`.CircuitTranspiler.transpile_circuit()` method. Refer to the method's documentation or :ref:`Transpilation <transpilation>` for more detailed information.

    The main stages of this process are: **1.** Routing, **2.** Canceling Hermitian pairs, **3.** Translate to native gates, **4.** Correcting Drag phases, **5** Optimize Drag gates, **6.** Convert to pulse schedule.

    .. note ::

        Default steps are only: **3.**, **4.**, and **6.**, since they are always needed.

        To do Step **1.** set routing=True in transpilation_config (default behavior skips it).

        To do Steps **2.** and **5.** set optimize=True in transpilation_config (default behavior skips it)

    Args:
        circuit (Circuit | list[Circuit]): Qibo Circuit.
        runcard (str | dict): If a string, path to the YAML file containing the serialization of the Platform to be
            used. If a dictionary, the serialized platform to be used.
        nshots (int, optional): Number of shots to execute. Defaults to 1.
        transpilation_config (DigitalTranspilationConfig, optional): :class:`.DigitalTranspilationConfig` dataclass containing
            the configuration used during transpilation. Defaults to ``None`` (not changing any default value).
            Check the class:`.DigitalTranspilationConfig` documentation for the keys and values it can contain.

    Returns:
        Result | list[Result]: :class:`Result` class (or list of :class:`Result` classes) containing the results of the
            execution.

    |

    Example Usage:

    .. code-block:: python

        import numpy as np
        from qibo import Circuit, gates
        from qibo.transpiler import Sabre, ReverseTraversal
        from qililab.digital import DigitalTranspilationConfig
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
        transpilation = DigitalTranspilationConfig(routing=True, router=Sabre, placer=ReverseTraversal)

        # Execute with routing during the transpilation:
        probabilities = ql.execute(c, runcard="./runcards/galadriel.yml", transpilation_config=transpilation)
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
                transpilation_config=transpilation_config,
            )
            for circuit in tqdm(program, total=len(program))
        ]
        platform.disconnect()
        return results[0] if len(results) == 1 else results
    except Exception as e:
        platform.disconnect()
        raise e
