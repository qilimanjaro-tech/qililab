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
from typing import Any, Iterable

from qibo.models import Circuit
from tqdm.auto import tqdm

from qililab.platform.platform import Platform
from qililab.pulse.pulse_schedule import PulseSchedule
from qililab.result import Result

from .data_management import build_platform


def execute(program: Any | Circuit | Iterable[Circuit], runcard: str | dict, nshots: int = 1) -> Result | list[Result]:
    """Executes a Qibo circuit (or a list of circuits) with qililab and returns the results.

    Args:
        circuit (Circuit | list[Circuit] | Any): Qibo Circuit or any other language that can be translated with qbraid.
        runcard (str | dict): If a string, path to the YAML file containing the serialization of the Platform to be
            used. If a dictionary, the serialized platform to be used.
        nshots (int, optional): Number of shots to execute. Defaults to 1.

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
        c.add(gates.CNOT(2,0))
        c.add(gates.RY(4,np.pi / 4))
        c.add(gates.X(3))
        c.add(gates.M(*range(3)))
        c.add(gates.SWAP(4,2))
        c.add(gates.RX(1, 3*np.pi/2))

        probabilities = ql.execute(c, runcard="./runcards/galadriel.yml")
    """
    # Initialize platform and connect to the instruments
    platform: Platform = build_platform(runcard=runcard)
    platform.connect()

    # pylint: disable=protected-access
    if not hasattr(program, "__iter__"):
        translated_program: list[Circuit | PulseSchedule] = [platform._translate_language(program=program)]
    else:
        translated_program = [platform._translate_language(program=progrm) for progrm in program]

    # Execute circuit
    try:
        platform.initial_setup()
        platform.turn_on_instruments()
        results = [
            platform.execute(circuit, num_avg=1, repetition_duration=200_000, num_bins=nshots)
            for circuit in tqdm(translated_program, total=len(translated_program))
        ]
        platform.disconnect()
        return results[0] if len(results) == 1 else results
    except Exception as e:
        platform.disconnect()
        raise e
