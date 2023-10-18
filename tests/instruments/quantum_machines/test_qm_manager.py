"""This file tests the the ``qblox_d5a`` class"""
from unittest.mock import MagicMock, patch

import pytest

from qililab.instruments.quantum_machines import QMM

@pytest.fixture(name="mock_qmm")
def fixture_quantum_machines_manager(mock_qmm: MagicMock):
    """Return a mock instance of Quantum Machines Manager class"""
    return mock_qmm

@patch("qm.QuantumMachinesManager", autospec=True)
@pytest.fixture(name="qmm")
def fixture_qmm():
    """Fixture that returns an instance of a dummy Quantum Machines Manager."""
    return QMM(
        {
            "alias": "qmm",
            "qop_ip": "192.168.0.1",
            "qop_port": 80,
            "config": {},
            "firmware": "3.10.2"
        }
    )  # pylint: disable=abstract-class-instantiated


class TestQMM:
    """This class contains the unit tests for the ``QMM`` class."""

    def test_inital_setup_method(self, qmm: QMM):
        """Test initial_setup method"""
        qmm.initial_setup()

        assert 1==0
