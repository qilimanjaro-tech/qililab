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
experiment = ql.execute_qibo_circuit(c, runcard_name="galadriel", get_experiment_only=True)
# plot pulse schedule
figure = experiment.draw()
plt.show()
