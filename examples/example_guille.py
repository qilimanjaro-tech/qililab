"""Example guille distortions"""
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from qibo import gates
from qibo.models import Circuit

import qililab as ql

nqubits = 5
c = Circuit(nqubits)
for qubit in range(nqubits):
    c.add(gates.H(qubit))
c.add(gates.CZ(2, 0))
c.add(gates.RY(4, np.pi / 4))
c.add(gates.X(3))
c.add(gates.M(*range(3)))
c.add(gates.SWAP(4, 2))
c.add(gates.RX(1, 3 * np.pi / 2))

fname = os.path.abspath("")
os.environ["RUNCARDS"] = str(Path(fname) / "examples/runcards")
os.environ["DATA"] = str(Path(fname) / "data")

# configuration = ConnectionConfiguration(username="username", api_key="api_key")
# connection = API(configuration=configuration)

# load platform
runcard_name = "galadriel"

circuit = c
platform = ql.build_platform(name=runcard_name)

settings = ql.ExperimentSettings(
    hardware_average=1,
    repetition_duration=0,
    software_average=1,
)
options = ql.ExperimentOptions(
    loops=[],  # loops to run the experiment
    settings=settings,  # experiment settings
    name="experiment",  # name of the experiment (it will be also used for the results folder name)
)
# transpile and optimize circuit
circuit = ql.translate_circuit(circuit, optimize=True)
sample_experiment = ql.Experiment(
    platform=platform,  # platform to run the experiment
    circuits=[circuit],  # circuits to run the experiment
    options=options,  # experiment options
)

sample_experiment.build_execution()

for gate in circuit.queue:
    print(gate.name, gate.qubits)

figure = sample_experiment.draw()
plt.show()
