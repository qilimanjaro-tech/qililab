import os
from pathlib import Path

import matplotlib.pyplot as plt
from qibo.gates import RX, M, X
from qibo.models.circuit import Circuit

from qililab import Experiment, ExperimentOptions, ExperimentSettings, build_platform
from qililab.typings.enums import Parameter
from qililab.typings.execution import ExecutionOptions
from qililab.typings.loop import LoopOptions
from qililab.utils.loop import Loop
from qililab.utils.qibo_gates import Reset, Wait

# user_variables = {
#     'wait1': None,
#     'wait2': None
# }

# Define Circuit to execute
circuit = Circuit(1)
circuit.add(X(0))
circuit.add(Wait(0, n=100))
circuit.add(X(0))
circuit.add(Wait(0, n=300))
circuit.add(X(0))
circuit.add(M(0))

print(circuit.get_parameters())

circuit.set_parameters([500, 500])

print(circuit.get_parameters(format="dict"))

loop = Loop(alias="0", parameter=Parameter.GATE_PARAMETER, options=LoopOptions(start=40, stop=140, step=20))

# circuit.draw()

fname = os.path.abspath("")
os.environ["RUNCARDS"] = "/home/vyron/Projects/qilimanjaro/qililab/examples/runcards"
os.environ["DATA"] = str(Path(fname) / "data")

runcard_name = "golum_soprano"
platform = build_platform(name=runcard_name)

settings = ExperimentSettings(
    hardware_average=1000,
    repetition_duration=20_000,
    software_average=1,
)


execution_options = ExecutionOptions(
    set_initial_setup=True,
    automatic_connect_to_instruments=False,
    automatic_disconnect_to_instruments=False,
    automatic_turn_on_instruments=False,
    automatic_turn_off_instruments=False,
)

options = ExperimentOptions(
    loops=[loop],
    settings=settings,
    device_id=15,
    execution_options=execution_options,
    name="my test experiment",
)

sample_experiment = Experiment(
    platform=platform,  # platform to run the experiment
    circuits=[circuit],  # circuits to run the experiment
    options=options,  # experiment options
)

# sample_experiment.draw()
# plt.show()
