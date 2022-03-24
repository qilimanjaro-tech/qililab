import pytest
import qibo

from qililab.backend import QililabBackend
from qililab.circuit import HardwareCircuit
from qililab.gates import Identity, X, Y, Z
from qililab.platforms.qiliplatform import QiliPlatform


@pytest.fixture
def backend() -> QililabBackend:
    """Test of the QililabBackend class instantiation.
    This function is used as input to other backend tests.

    Returns:
        QililabBackend: Instance of the QililabBackend class.
    """
    return QililabBackend()


class TestBackend:
    """Unit tests checking the QililabBackend initialization steps and values"""

    def test_set_backend(self) -> None:
        """Test of the initialization of the qililab backend and qili platform using qibo.
        Run the qibo.set_backend function to activate qililab backend and qili platform."""
        # FIXME: Need to add backend in qibo's profiles.yml file
        backend = {
            "name": "qililab",
            "driver": "qililab.backend.QililabBackend",
            "minimum_version": "0.0.1.dev0",
            "is_hardware": True,
        }
        qibo.K.profile["backends"].append(backend)
        qibo.set_backend(backend="qililab", platform="qili")
        assert isinstance(qibo.K.active_backend, QililabBackend)
        assert isinstance(qibo.K.platform, QiliPlatform)

    def test_set_platform(self, backend: QililabBackend) -> None:
        """Test the set_platform method of the QililabBackend class.

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        backend.set_platform("qili")
        assert isinstance(backend.platform, QiliPlatform)

    def test_get_platform(self, backend: QililabBackend) -> None:
        """Test the get_platform method of the QililabBackend class.

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        backend.set_platform("qili")
        name = backend.get_platform()
        assert name == "qili"

    def test_circuit_class(self, backend: QililabBackend) -> None:
        """Test the circuit_class method of the QililabBackend class.

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        assert backend.circuit_class() == HardwareCircuit

    def test_create_gate(self, backend: QililabBackend) -> None:
        """Test the create_gate method of the QililabBackend class.

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        for gate in [Identity, X, Y, Z]:
            assert isinstance(backend.create_gate(gate), gate)
