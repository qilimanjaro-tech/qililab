from qibo.models import Circuit

import qililab as ql
from qililab.experiment.circuit_experiment import CircuitExperiment
from qililab.platform import Platform


def execute(circuit: Circuit, platform: str | Platform, nshots=1):
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

    if isinstance(platform, str):
        # create platform
        platform = ql.build_platform(name=platform)

    settings = ql.ExperimentSettings(
        hardware_average=1, repetition_duration=200000, software_average=1, num_bins=nshots
    )
    options = ql.ExperimentOptions(settings=settings)

    # create experiment with options
    sample_experiment = CircuitExperiment(platform=platform, circuits=[circuit], options=options)

    try:
        results = sample_experiment.execute(save_experiment=False, save_results=False)
    except Exception:
        sample_experiment.disconnect()
        raise

    return results
