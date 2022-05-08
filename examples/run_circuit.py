"""Run circuit"""
import qibo

from qililab.circuit import HardwareCircuit
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.gates import I, X, Y

# FIXME: Need to add backend in qibo's profiles.yml file
backend = {
    "name": "qililab",
    "driver": "qililab.backend.QililabBackend",
    "minimum_version": "0.0.1.dev0",
    "is_hardware": True,
}
qibo.K.profile["backends"].append(backend)
# ------------------------------------------------------


def run_circuit():
    """Load the platform 'platform_0' from the DB."""
    # Using qibo (needed when using qibo circuits)
    qibo.set_backend(backend="qililab", platform=DEFAULT_PLATFORM_NAME)
    # Using PLATFORM_MANAGER_DB
    circuit = HardwareCircuit(3)
    circuit.add(I(0, 1, 2))
    circuit.add(X(2))
    circuit.add(Y(0))
    circuit.execute()


if __name__ == "__main__":
    run_circuit()
