"""This file tests the the ``qmm_controller`` class"""
from unittest.mock import MagicMock

import pytest
import numpy as np
from qililab.instrument_controllers.quantum_machines import QMMController
from qililab.instruments.quantum_machines import QMM
from qililab.settings import Settings

@pytest.fixture(name="qmm")
def fixture_qmm():
    """Fixture that returns an instance a qililab wrapper for Quantum Machines Manager."""
    qmm = QMM(
        {"alias": "qmm", "qop_ip": "192.168.0.1", "qop_port": 80, "config": {}, "firmware": "3.10.2"}
    )  # pylint: disable=abstract-class-instantiated
    qmm.device = MagicMock
    qmm.qm = MagicMock

    return qmm

@pytest.fixture(name="qmm_controller")
def fixture_qmm_controller(qmm: QMM):
    """Fixture that returns an instance a qililab wrapper for Quantum Machines Manager."""
    settings = {
        "alias": "qmm_controller",
        "connection": "127.0.0.1",
        "modules": [qmm]
    }

    return QMMController(settings=settings, loaded_instruments=[QMM])  # pylint: disable=abstract-class-instantiated


class TestQMM:
    """This class contains the unit tests for the ``QMMController`` class."""

    def test_settings(self, qmm_controller: QMMController):
        """Test QMMControllerSettings have been set correctly"""

        assert isinstance(qmm_controller.settings, Settings)
