"""Run circuit experiment"""
import os
from pathlib import Path

import matplotlib.pyplot as plt
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

    # Define loops
    freq_loop = Loop(alias="rs_1", parameter=Parameter.FREQUENCY, start=7.3255e9, stop=7.3280e9, step=0.02e6)
    att_loop = Loop(alias="attenuator", parameter=Parameter.ATTENUATION, start=10, stop=65, step=0.5, loop=freq_loop)

    # Change settings
    settings = Experiment.ExperimentSettings()
    # settings.software_average = 5
    settings.repetition_duration = 20000

    # Instantiate Experiment
    punchout = Experiment(
        platform=platform, sequences=circuit, loop=att_loop, connection=connection, name="punchout", settings=settings
    )

    # Change parameters
    punchout.set_parameter(
        alias="M", parameter=Parameter.AMPLITUDE, value=1
    )  # you are changing here the parameters for punchout. Before the parameters for cavity spectroscopy was changed so
    # the platform parameter of readout amplitude keeps being 0.4.
    # punchout.set_parameter(instrument=Instrument.ATTENUATOR, id_=1, parameter=Parameter.ATTENUATION, value=15)
    # IMPORTANT: Need to disable Qblox synchronization since we are only using the QRM
    punchout.set_parameter(
        alias="QRM", parameter=Parameter.SYNC_ENABLED, value=False
    )  # this is because we don't want the qubit awg to interfere here.

    punchout.set_parameter(alias="M", parameter=Parameter.DURATION, value=8000)
    punchout.set_parameter(alias="QRM", parameter=Parameter.INTEGRATION_LENGTH, value=8000)

    # Execute experiment
    results = punchout.execute()

    # Get acquisitions (shape = [4, loops_shape, num_sequences]
    i, q, amplitude, phase = results.acquisitions()
    attenuation, freq = results.ranges

    amplitude *= 10 ** (attenuation[:, None] / 20)

    # Plot
    plt.figure(figsize=(10, 5))
    plt.pcolormesh(
        freq / 1e9, attenuation, amplitude, shading="nearest", cmap=plt.colormaps["seismic"]
    )  # , norm=colors.LogNorm())
    plt.ylabel("Attenuation (dBm)")
    plt.xlabel("LO frequency (GHz)")
    plt.ylim(plt.ylim()[::-1])
    cbar = plt.colorbar()
    cbar.set_label("Amplitude (V)", rotation=270, labelpad=15)
    plt.minorticks_on()
    plt.savefig("att_vs_freq.pdf", dpi=200)


if __name__ == "__main__":
    api = API()
    # api.list_devices()
    # api.release_device(device_id=9)
    run_circuit(connection=api)
