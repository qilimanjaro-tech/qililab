"""Run circuit experiment"""
import os
from pathlib import Path

from qibo.core.circuit import Circuit
from qibo.gates import M, X
from qiboconnection.api import API

from qililab import Experiment, ExperimentOptions, ExperimentSettings, build_platform
from qililab.typings.enums import Parameter
from qililab.typings.execution import ExecutionOptions
from qililab.typings.loop import LoopOptions
from qililab.utils.loop import Loop

os.environ["RUNCARDS"] = str(Path(__file__).parent / "runcards")
os.environ["DATA"] = str(Path(__file__).parent / "data")

SAURON_SOPRANO = 15


def run_circuit(connection: API | None = None):
    """Load the platform 'galadriel' from the DB."""
    runcard_name = "sauron_soprano"
    platform = build_platform(name=runcard_name)

    # platform.connect_and_set_initial_setup(
    #     connection=connection, device_id=SAURON_SOPRANO, automatic_turn_on_instruments=True
    # )

    circuit = Circuit(1)
    # circuit.add(X(0))
    circuit.add(M(0))

    lo_freq_loop = Loop(
        alias="feedline_input_output_bus",
        parameter=Parameter.LO_FREQUENCY,
        options=LoopOptions(start=6.0e09, stop=6.5e09, num=10),
    )

    settings = ExperimentSettings(
        hardware_average=1000,
        repetition_duration=20_000,
        software_average=1,
    )

    execution_options = ExecutionOptions(
        set_initial_setup=True,
        automatic_connect_to_instruments=True,
        automatic_disconnect_to_instruments=True,
        automatic_turn_on_instruments=True,
        automatic_turn_off_instruments=True,
    )

    options = ExperimentOptions(
        loops=[lo_freq_loop],  # loops to run the experiment
        settings=settings,  # experiment settings
        connection=connection,  # remote connection for live plotting
        device_id=SAURON_SOPRANO,  # device identifier to block and release for remote executions
        execution_options=execution_options,
        name="my test experiment",
    )

    sample_experiment = Experiment(
        platform=platform,  # platform to run the experiment
        circuits=[circuit],  # circuits to run the experiment
        options=options,  # experiment options
    )
    sample_experiment.set_parameter(parameter=Parameter.SYNC_ENABLED, value=False, alias="QRM", channel_id=0)
    results = sample_experiment.execute()
    # print(results)
    print(results.acquisitions())

    # platform.disconnect(automatic_turn_off_instruments=True)


if __name__ == "__main__":
    # configuration = ConnectionConfiguration(
    #     username="user",
    #     api_key="api_key",
    # )
    # api = API(configuration=configuration)
    api = API()
    api.release_device(device_id=SAURON_SOPRANO)
    run_circuit(connection=api)
