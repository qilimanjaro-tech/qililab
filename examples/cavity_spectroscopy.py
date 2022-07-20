"""Run circuit experiment"""
import os
from pathlib import Path

from qibo.core.circuit import Circuit
from qibo.gates import M
from qiboconnection.api import API

from qililab import build_platform
from qililab.experiment import Experiment
from qililab.typings import Parameter
from qililab.utils import Loop

os.environ["RUNCARDS"] = str(Path(__file__).parent / "runcards")
os.environ["DATA"] = str(Path(__file__).parent / "data")


def run_circuit(connection: API | None = None):
    """Load the platform 'galadriel' from the DB."""
    platform = build_platform(name="galadriel_controller")
    # Define Circuit to execute
    circuit = Circuit(1)
    circuit.add(M(0))

    # Define loops (optional)
    loop_freq = Loop(alias="resonator", parameter=Parameter.FREQUENCY, start=7.32e9, stop=7.332e9, step=0.2e5)

    # Change settings (optional)
    settings = Experiment.ExperimentSettings()
    # settings.hardware_average=1024*3
    # settings.software_average=3
    settings.repetition_duration = 20000

    # Instantiate Experiment class
    cavity_spectroscopy = Experiment(
        platform=platform,
        sequences=circuit,
        loop=loop_freq,
        name="cavity_spectroscopy",
        connection=connection,
        settings=settings,
        plot_y_label="Voltage",
    )  # if you don't want to define any settings just remove settings=settings.

    # Change any parameters (optional)
    cavity_spectroscopy.set_parameter(alias="M", parameter=Parameter.AMPLITUDE, value=1)  # by default was 0.4.
    # IMPORTANT: Need to disable Qblox synchronization since we are only using the QRM
    cavity_spectroscopy.set_parameter(alias="QRM", parameter=Parameter.SYNC_ENABLED, value=False)
    cavity_spectroscopy.set_parameter(alias="attenuator", parameter=Parameter.ATTENUATION, value=10)
    cavity_spectroscopy.set_parameter(alias="M", parameter=Parameter.DURATION, value=8000)
    cavity_spectroscopy.set_parameter(alias="QRM", parameter=Parameter.INTEGRATION_LENGTH, value=8000)

    # Execute experiment
    results = (
        cavity_spectroscopy.execute()
    )  # connection is used to do the life plotting but you can run it without it if you don't want life plotting.
    print(results.acquisitions())


if __name__ == "__main__":
    api = API()
    run_circuit(connection=api)
