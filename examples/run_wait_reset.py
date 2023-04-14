import os
from pathlib import Path

import matplotlib.pyplot as plt
from qibo.gates import RX, M, X
from qibo.models.circuit import Circuit

from qililab import Experiment, ExperimentOptions, ExperimentSettings, build_platform
from qililab.config import logger
from qililab.typings.enums import Parameter
from qililab.typings.execution import ExecutionOptions
from qililab.typings.loop import LoopOptions
from qililab.utils.loop import Loop
from qililab.utils.qibo_gates import Reset, Wait

logger.setLevel(30)


# Define Circuit to execute
circuit = Circuit(1)
circuit.add(X(0))
circuit.add(Wait(0, n=100))
circuit.add(M(0))

loop = Loop(alias="0", parameter=Parameter.GATE_PARAMETER, options=LoopOptions(start=0, stop=400, step=12))

frequency_loop_options = LoopOptions(start=6e9, stop=7e9, num=101)
frequency_loop = Loop(alias="rs_1", parameter=Parameter.LO_FREQUENCY, options=frequency_loop_options)
# circuit.draw()

os.environ["RUNCARDS"] = "/home/qilimanjaro/Documents/GitHubRepos/qililab/examples/runcards"
os.environ["DATA"] = "/home/qilimanjaro/Documents/data"

runcard_name = "golum_soprano"
platform = build_platform(name=runcard_name)
platform.connect_and_set_initial_setup()

settings = ExperimentSettings(hardware_average=10000, repetition_duration=200000)


execution_options = ExecutionOptions(
    set_initial_setup=True,
    automatic_connect_to_instruments=False,
    automatic_disconnect_to_instruments=False,
    automatic_turn_on_instruments=False,
    automatic_turn_off_instruments=False,
)

options = ExperimentOptions(
    loops=[frequency_loop],
    settings=settings,
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

store_scope = False
sample_experiment.set_parameter(
    alias="QRM",
    parameter=Parameter.SCOPE_STORE_ENABLED,
    value=store_scope,
    channel_id=0,
)


sample_experiment.execute()
# sample_experiment.draw()
# plt.show()
