"""Run circuit experiment"""
import os
from pathlib import Path

from qiboconnection.api import API

from qililab import load

os.environ["RUNCARDS"] = str(Path(__file__).parent / "runcards")
os.environ["DATA"] = str(Path(__file__).parent / "data")


def run_circuit(connection: API | None = None):
    """Load the platform 'galadriel' from the DB."""
    # experiment, results = load(path="./examples/data/20220725_121101_allxy_cmap")
    experiment, results = load(path="./examples/data/20220730_114929_qubit_spectroscopy")
    acquisitions = results.acquisitions(mean=False)
    i, q, amplitude, phase = acquisitions
    ampl_pulse, fq_pulse = results.ranges
    print(len(ampl_pulse), len(fq_pulse), len(acquisitions), len(i), len(q), len(amplitude), len(phase))


if __name__ == "__main__":
    api = API()
    run_circuit(connection=api)
