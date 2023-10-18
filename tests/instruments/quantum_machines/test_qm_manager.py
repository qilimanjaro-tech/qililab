"""This file tests the the ``qblox_d5a`` class"""
from unittest.mock import MagicMock, patch
import pytest

from qililab.instruments.quantum_machines import QMM
from qililab.settings import Settings

@patch("qm.QuantumMachinesManager", autospec=True)
@pytest.fixture(name="qmm")
def fixture_qmm():
    """Fixture that returns an instance of a dummy Quantum Machines Manager."""
    qmm = QMM(
        {
            "alias": "qmm",
            "qop_ip": "192.168.0.1",
            "qop_port": 80,
            "config": {},
            "firmware": "3.10.2"
        }
    )  # pylint: disable=abstract-class-instantiated
    qmm.device = MagicMock

    return qmm


class TestQMM:
    """This class contains the unit tests for the ``QMM`` class."""

    def test_settings(self, qmm: QMM):
        """Test QMMSettings have been set correctly"""

        assert isinstance(qmm.settings, Settings)
