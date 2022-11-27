"""Run circuit experiment"""
import os
from pathlib import Path

from qibo.core.circuit import Circuit
from qibo.gates import M, X
from qiboconnection.api import API
from qiboconnection.connection import ConnectionConfiguration

from qililab import build_platform
from qililab.experiment import Experiment
from qililab.typings import Parameter
from qililab.typings.execution import ExecutionOptions
from qililab.typings.experiment import ExperimentOptions
from qililab.typings.loop import LoopOptions
from qililab.utils import Loop

os.environ["RUNCARDS"] = str(Path(__file__).parent / "runcards")
os.environ["DATA"] = str(Path(__file__).parent / "data")


def run_circuit(connection: API | None = None):
    """Load the platform 'galadriel' from the DB."""
    platform = build_platform(name="template_base_runcard_soprano")
    print(platform)
    print(platform.schema)

    # circuit = Circuit(1)
    # circuit.add(X(0))
    # circuit.add(M(0))

    # loop = Loop(
    #     alias="D5a",
    #     parameter=Parameter.VOLTAGE,
    #     options=LoopOptions(start=1.0, stop=1.5, num=10, channel_id=0),
    # )
    # loop = Loop(
    #     alias="S4g",
    #     parameter=Parameter.CURRENT,
    #     options=LoopOptions(start=0.0, stop=1.5, num=10, channel_id=3),
    # )
    # inner_loop = Loop(
    #     alias="bus_control",
    #     parameter=Parameter.GAIN,
    #     options=LoopOptions(start=0.5, stop=1.0, num=5, channel_id=0),
    # )
    # loop = Loop(
    #     alias="bus_control",
    #     parameter=Parameter.FREQUENCIES,
    #     options=LoopOptions(start=1.0e08, stop=1.5e08, num=10, channel_id=0),
    #     loop=inner_loop,
    # )
    # loop = Loop(
    #     alias="bus_control",
    #     parameter=Parameter.FREQUENCIES,
    #     options=LoopOptions(start=1.0e08, stop=1.5e08, num=10, channel_id=0),
    # )
    # loop = Loop(
    #     alias="bus_control",
    #     parameter=Parameter.FREQUENCY,
    #     options=LoopOptions(start=6.0e09, stop=6.5e09, num=10, channel_id=0),
    # )

    # experiment = Experiment(
    #     platform=platform,
    #     schedules=circuit,
    #     options=ExperimentOptions(
    #         loops=[loop],
    #         name="experiment_demo",
    #         execution_options=ExecutionOptions(
    #             set_initial_setup=False,
    #             automatic_connect_to_instruments=False,
    #             automatic_disconnect_to_instruments=False,
    #             automatic_turn_on_instruments=False,
    #             automatic_turn_off_instruments=False,
    #         ),
    #     ),
    # )

    # results = experiment.execute()
    # print(results)
    # print(results.acquisitions())


if __name__ == "__main__":
    # configuration = ConnectionConfiguration(
    #     username="user",
    #     api_key="api_key",
    # )
    # api = API(configuration=configuration)
    api = API()
    run_circuit(connection=api)
