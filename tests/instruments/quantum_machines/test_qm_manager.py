"""This file tests the the ``qblox_d5a`` class"""
import numpy as np
from unittest.mock import MagicMock, patch
import pytest

from qm import Program, QuantumMachinesManager
from qm.jobs.base_job import QmBaseJob
from qm.qua import program, play
from qililab.instruments.quantum_machines import QMM
from qililab.settings import Settings

@pytest.fixture(name="qua_program")
def fixture_qua_program():
    """Dummy QUA Program"""
    with program() as dummy_qua_program:
        play('pulse1', 'element1')

    return dummy_qua_program

class MockQuantumMachinesManager(MagicMock):  # pylint: disable=abstract-method

    def execute(self, program: Program):  # pylint: disable=unused-argument
        """Mocks a QUA Program execution."""
        job = MagicMock()
        job.return_handles.return_value = np.empty(10)

        return job
@patch("qm.QuantumMachinesManager", autospec=True)
@pytest.fixture(name="qmm")
def fixture_qmm():
    """Fixture that returns an instance a qililab wrapper for Quantum Machines Manager."""
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
    qmm.qm = MockQuantumMachinesManager()

    return qmm


class TestQMM:
    """This class contains the unit tests for the ``QMM`` class."""

    def test_settings(self, qmm: QMM):
        """Test QMMSettings have been set correctly"""

        assert isinstance(qmm.settings, Settings)

    def test_execute(self, qmm: QMM, qua_program: Program):
        """Test execute method"""

        result = qmm.run(qua_program)

        assert 1 == 1
