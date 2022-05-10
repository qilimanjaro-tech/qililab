"""Run circuit experiment"""
import matplotlib.pyplot as plt
from qibo.core.circuit import Circuit
from qibo.gates import I, M, X, Y
import matplotlib.pyplot as plt

from qililab import Experiment
from qililab.constants import DEFAULT_PLATFORM_NAME


def load_experiment():
    """Load the platform 'platform_0' from the DB."""
    # Using PLATFORM_MANAGER_DB
    circuit = Circuit(1)
    # circuit.add(X(0))
    circuit.add(M(0))
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequence=circuit)
    experiment.add_parameter_to_loop(
        category="signal_generator", id_=1, parameter="frequency", start=7300000000.0, stop=7313000000.0, num=50
    )
    results = experiment.execute()
    voltages = []
    for result in results:
        voltages.append(result[0].voltages())
    plt.plot(voltages)
    plt.savefig(fname="test.png")




if __name__ == "__main__":
    load_experiment()
