"""Run circuit experiment"""
import matplotlib.pyplot as plt
from qibo.core.circuit import Circuit
from qibo.gates import I, M, X, Y

from qililab import Experiment
from qililab.constants import DEFAULT_PLATFORM_NAME


def load_experiment():
    """Load the platform 'platform_0' from the DB."""
    # Using PLATFORM_MANAGER_DB
    circuit = Circuit(1)
    circuit.add(I(0))
    circuit.add(X(0))
    circuit.add(Y(0))
    circuit.add(M(0))
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequence=circuit)
    experiment.add_parameter_to_loop(
        category="signal_generator", id_=1, parameter="frequency", start=3544000000, stop=3744000000, step=10000000
    )
    figure = experiment.draw(resolution=0.1)
    figure.show()
    plt.show()


if __name__ == "__main__":
    load_experiment()
