import os
from pathlib import Path

from qibo.models import Circuit

import qililab as ql


def execute(circuit: Circuit, runcard_name: str):
    """Execute a qibo with qililab and native gates

    Args:
        circuit (Circuit): qibo circuit
        runcard_name (str): name of the runcard to be loaded
    Returns:
        Results: ``Results`` class containing the experiment results

    Example Usage:

    ```python
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

    probabilities = ql.execute(c, runcard_name="galadriel")
    ```

    """
    # transpile and optimize circuit
    circuit = ql.translate_circuit(circuit, optimize=True)

    # create platform
    platform = ql.build_platform(name=runcard_name)

    settings = ql.ExperimentSettings(
        hardware_average=1,
        repetition_duration=0,
        software_average=1,
    )
    options = ql.ExperimentOptions(
        loops=[],  # loops to run the experiment
        settings=settings,  # experiment settings
    )

    # create experiment with options
    sample_experiment = ql.Experiment(
        platform=platform,  # platform to run the experiment
        circuits=[circuit],  # circuits to run the experiment
        options=options,  # experiment options
    )

    return sample_experiment.execute(save_results=False)
