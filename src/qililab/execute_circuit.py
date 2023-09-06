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
from .experiment.experiment import Experiment
from .transpiler import translate_circuit
from .typings import ExperimentOptions, ExperimentSettings


def execute(circuit: Circuit, platform_path: str, nshots: int = 1):
    """Execute a qibo with qililab and native gates

    Args:
        circuit (Circuit): Qibo Circuit.
        platform_path (str): Path to the YAML file containing the serialization of the Platform to be used.
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

        probabilities = ql.execute(c, platform_path="./runcards/galadriel.yml")


    """
    # transpile and optimize circuit
    circuit = translate_circuit(circuit, optimize=True)

    # create platform
    platform = build_platform(path=platform_path)

    settings = ExperimentSettings(hardware_average=1, repetition_duration=200000, software_average=1, num_bins=nshots)
    options = ExperimentOptions(settings=settings)

    # create experiment with options
    sample_experiment = Experiment(platform=platform, circuits=[circuit], options=options)

    return sample_experiment.execute(save_experiment=False, save_results=False)
