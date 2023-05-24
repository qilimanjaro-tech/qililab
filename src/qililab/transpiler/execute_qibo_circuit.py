import os
from pathlib import Path

from qibo.models import Circuit

import qililab as ql


def execute_qibo_circuit(circuit: Circuit, runcard_name: str, get_experiment_only: bool):
    """Transpile a qibo circuit to native gates and run it with qililab

    Args:
        circuit (Circuit): qibo circuit
        runcard_name (str): name of the runcard to be loaded
        get_experiment_only (bool): return sample experiment instead of running it

    Returns:
        Results | Experiment: ``Results`` class containing the experiment results | sampple experiment

    Example Usage:

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

    probabilities = execute_qibo_circuit(c, runcard_name="galadriel")


    To plot pulse schedules:
    do all of the above with get_experiment_only = True, then:
        experiment = execute_qibo_circuit(c, runcard_name="galadriel")
        experiment.draw()
    """

    fname = os.path.abspath("")
    os.environ["RUNCARDS"] = str(Path(fname) / "examples/runcards")
    os.environ["DATA"] = str(Path(fname) / "data")
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
    # transpile and optimize circuit
    circuit = ql.translate_circuit(circuit, optimize=True)
    sample_experiment = ql.Experiment(
        platform=platform,  # platform to run the experiment
        circuits=[circuit],  # circuits to run the experiment
        options=options,  # experiment options
    )
    if get_experiment_only:
        sample_experiment.build_execution()
        return sample_experiment

    return sample_experiment.execute().probabilities
