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
from qililab.utils import Loop

os.environ["RUNCARDS"] = str(Path(__file__).parent / "runcards")
os.environ["DATA"] = str(Path(__file__).parent / "data")


def run_circuit(connection: API | None = None):
    """Load the platform 'galadriel' from the DB."""
    platform = build_platform(name="template_qblox_sequencers")
    # print(platform)
    circuit = Circuit(1)
    circuit.add(X(0))
    circuit.add(M(0))
    # loop = Loop(alias="QCM", parameter=Parameter.FREQUENCIES, start=1.e+08, stop=1.5e+08, step=0.1e6)
    # loop = Loop(alias="QCM", parameter=Parameter.FREQUENCIES, start=1.0e08, stop=1.5e08, num=10, channel_id=1)
    loop = Loop(alias="QCM", parameter=Parameter.FREQUENCIES, start=1.0e08, stop=1.5e08, num=10, channel_id=0)
    # loop = Loop(alias="bus_control", parameter=Parameter.FREQUENCIES, start=1.0e08, stop=1.5e08, num=10, channel_id=0)
    # loop = Loop(alias="bus_control", parameter=Parameter.FREQUENCY, start=6.0e09, stop=6.5e09, num=10, channel_id=0)

    experiment = Experiment(platform=platform, sequences=circuit, loops=[loop])

    results = experiment.execute()
    print(results)
    # print(results.acquisitions())


if __name__ == "__main__":
    # configuration = ConnectionConfiguration(
    #     username="user",
    #     api_key="api_key",
    # )
    # api = API(configuration=configuration)
    api = API()
    run_circuit(connection=api)
