import pytest
import qibo
from qibo.models import Circuit

from qililab.backend import QililabBackend
from qililab.circuit import HardwareCircuit
from qililab.gates import I, X, Y, Z
from qililab.platforms import Platform


@pytest.fixture(name="backend")
def fixture_backend() -> QililabBackend:
    """Load QililabBackend using Qibo.

    Returns:
        QililabBackend: Instance of the QililabBackend class.
    """
    # FIXME: Need to add backend in qibo's profiles.yml file
    backend = {
        "name": "qililab",
        "driver": "qililab.backend.QililabBackend",
        "minimum_version": "0.0.1.dev0",
        "is_hardware": True,
    }
    qibo.K.profile["backends"].append(backend)
    qibo.set_backend(backend="qililab", platform="platform_0")
    return qibo.K.active_backend


class TestBackend:
    """Unit tests checking the QililabBackend attributes and methods"""

    def test_set_backend(self, backend: QililabBackend):
        """Test of the initialization of the qililab backend and qili platform using qibo.
        Run the qibo.set_backend function to activate qililab backend and qili platform."""
        assert isinstance(backend, QililabBackend)
        assert isinstance(qibo.K.active_backend, QililabBackend)
        assert isinstance(qibo.K.platform, Platform)

    def test_set_platform_using_default_platform(self, backend: QililabBackend):
        """Test the set_platform method of the QililabBackend class using platform "platform_0".

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        backend.set_platform("platform_0")
        assert isinstance(backend.platform, Platform)

    def test_set_platform_using_unknown_platform(self, backend: QililabBackend):
        """Test the set_platform method of the QililabBackend class using an unknown platform.

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        with pytest.raises(FileNotFoundError):
            backend.set_platform("unknown_platform")

    def test_get_platform(self, backend: QililabBackend):
        """Test the get_platform method of the QililabBackend class.

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        backend.set_platform("platform_0")
        name = backend.get_platform()
        assert name == "platform_0"

    def test_circuit_class(self, backend: QililabBackend):
        """Test the circuit_class method of the QililabBackend class.

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        circuit = Circuit(1)
        assert isinstance(circuit, HardwareCircuit)
        assert backend.circuit_class() == HardwareCircuit

    @pytest.mark.parametrize("gate", [I, X, Y, Z])
    def test_create_gate(self, backend: QililabBackend, gate):
        """Test the create_gate method of the QililabBackend class with the I, X, Y and Z gates.

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        assert isinstance(backend.create_gate(gate, 0), gate)
