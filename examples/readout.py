"""Run circuit experiment"""
import os
from pathlib import Path

from qibo.core.circuit import Circuit
from qibo.gates import I, M, X
from qiboconnection.api import API

from qililab import build_platform
from qililab.constants import GALADRIEL_DEVICE_ID
from qililab.experiment import Experiment
from qililab.typings import Parameter
from qililab.utils import Loop

os.environ["RUNCARDS"] = str(Path(__file__).parent / "runcards")
os.environ["DATA"] = str(Path(__file__).parent / "data")


def run_circuit(connection: API | None = None):
    """Load the platform 'galadriel' from the DB."""
    platform = build_platform(name="galadriel")
    # Define Circuit to execute
    circuit_0 = Circuit(1)
    circuit_0.add(I(0))
    circuit_0.add(M(0))
    circuit_1 = Circuit(1)
    circuit_1.add(X(0))
    circuit_1.add(M(0))
    circuits = [circuit_0, circuit_1]
    settings = Experiment.ExperimentSettings()
    settings.hardware_average = 1
    # Define loops
    intime_ro_loop = Loop(alias="M", parameter=Parameter.DURATION, start=200, stop=4000, step=100)

    # Instantiate Experiment
    ro_calibration_time = Experiment(
        platform=platform,
        sequences=circuits,
        loops=[intime_ro_loop],
        name="RO_calibration_ampl",
        connection=connection,
        device_id=GALADRIEL_DEVICE_ID,
        settings=settings,
    )
    # Set calibrated attenuation
    ro_calibration_time.set_parameter(alias="attenuator", parameter=Parameter.ATTENUATION, value=32)
    # Set calibrated readout amplitude
    ro_calibration_time.set_parameter(alias="M", parameter=Parameter.AMPLITUDE, value=0.85)
    # Set calibrated readout frequency
    ro_calibration_time.set_parameter(alias="resonator", parameter=Parameter.FREQUENCY, value=7.3274e09)
    # Set X pulse amplitude and duration extracted by doing a 2D Rabi
    ro_calibration_time.set_parameter(alias="X", parameter=Parameter.AMPLITUDE, value=0.9)
    ro_calibration_time.set_parameter(alias="X", parameter=Parameter.DURATION, value=128)
    ro_calibration_time.set_parameter(alias="QCM", parameter=Parameter.NUM_BINS, value=4000)
    ro_calibration_time.set_parameter(alias="QRM", parameter=Parameter.NUM_BINS, value=4000)
    # Change timeout if program duration is longer than 1 minute. Program duration is: hardware_avg * num_bins * repetition_duration
    ro_calibration_time.set_parameter(alias="QRM", parameter=Parameter.SEQUENCE_TIMEOUT, value=2)
    results = ro_calibration_time.execute()
    print(results.acquisitions())


if __name__ == "__main__":
    api = API()
    run_circuit(connection=api)
