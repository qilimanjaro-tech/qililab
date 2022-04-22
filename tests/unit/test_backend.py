import ntpath
from io import TextIOWrapper
from unittest.mock import MagicMock, patch

import pytest

from qililab.backend import QililabBackend
from qililab.circuit import HardwareCircuit
from qililab.gates import I, X, Y, Z
from qililab.platform.platform import Platform

from .data import MockedSettingsHashTable


@pytest.fixture(name="backend")
def fixture_backend() -> QililabBackend:
    """Load QililabBackend.

    Returns:
        QililabBackend: Instance of the QililabBackend class.
    """

    return QililabBackend()


def yaml_safe_load_side_effect(stream: TextIOWrapper):
    """Side effect for the function safe_load of yaml module."""
    filename = ntpath.splitext(ntpath.basename(stream.name))[0]
    return MockedSettingsHashTable.get(name=filename)


@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
class TestBackend:
    """Unit tests checking the QililabBackend attributes and methods"""

    def test_set_platform_using_default_platform(self, mock_load: MagicMock, backend: QililabBackend):
        """Test the set_platform method of the QililabBackend class using platform "platform_0".

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        backend.set_platform("platform_0")
        mock_load.assert_called()
        assert isinstance(backend.platform, Platform)

    def test_set_platform_using_unknown_platform(self, mock_load: MagicMock, backend: QililabBackend):
        """Test the set_platform method of the QililabBackend class using an unknown platform.

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        with pytest.raises(FileNotFoundError):
            backend.set_platform("unknown_platform")

    def test_get_platform(self, mock_load: MagicMock, backend: QililabBackend):
        """Test the get_platform method of the QililabBackend class.

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        backend.set_platform("platform_0")
        name = backend.get_platform()
        mock_load.assert_called()
        assert name == "platform"

    def test_circuit_class(self, mock_load: MagicMock, backend: QililabBackend):
        """Test the circuit_class method of the QililabBackend class.

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        assert backend.circuit_class() == HardwareCircuit
        mock_load.assert_not_called()

    @pytest.mark.parametrize("gate", [I, X, Y, Z])
    def test_create_gate(self, mock_load: MagicMock, backend: QililabBackend, gate):
        """Test the create_gate method of the QililabBackend class with the I, X, Y and Z gates.

        Args:
            backend (QililabBackend): Instance of the QililabBackend class.
        """
        assert isinstance(backend.create_gate(gate, 0), gate)
        mock_load.assert_not_called()
