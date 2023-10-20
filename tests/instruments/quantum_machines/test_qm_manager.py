"""This file tests the the ``qblox_d5a`` class"""
from unittest.mock import MagicMock

import numpy as np
import pytest
from qm import Program
from qm.qua import play, program

from qililab.instruments.quantum_machines import QMM
from qililab.result.quantum_machines_results import QuantumMachinesResult
from qililab.settings import Settings


@pytest.fixture(name="qua_program")
def fixture_qua_program():
    """Dummy QUA Program"""
    with program() as dummy_qua_program:
        play("pulse1", "element1")

    return dummy_qua_program


@pytest.fixture(name="qmm")
def fixture_qmm():
    """Fixture that returns an instance a qililab wrapper for Quantum Machines Manager."""
    qmm = QMM(
        {"alias": "qmm", "qop_ip": "192.168.0.1", "qop_port": 80, "config": {}, "firmware": "3.10.2"}
    )  # pylint: disable=abstract-class-instantiated
    qmm.device = MagicMock
    qmm.qm = MagicMock
    result = QuantumMachinesResult(qm_raw_results=np.zeros((2, 10)))
    qmm.run = MagicMock(return_value=result)
    qmm.simulate = MagicMock(return_value=result)

    return qmm


class TestQMM:
    """This class contains the unit tests for the ``QMM`` class."""

    def test_settings(self, qmm: QMM):
        """Test QMMSettings have been set correctly"""

        assert isinstance(qmm.settings, Settings)

    def test_execute(self, qmm: QMM, qua_program: Program):
        """Test execute method"""
        result = qmm.run(qua_program)

        assert isinstance(result, QuantumMachinesResult)
        assert result.array.shape == (2, 10)

    def test_simulate(self, qmm: QMM, qua_program: Program):
        """Test simulate method"""
        result = qmm.simulate(qua_program)

        assert isinstance(result, QuantumMachinesResult)
        assert result.array.shape == (2, 10)
