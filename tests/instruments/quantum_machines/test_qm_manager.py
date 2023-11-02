"""This file tests the the ``qm_manager`` class"""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qm import Program
from qm.qua import play, program

from qililab.instruments.quantum_machines import QMM
from qililab.result.quantum_machines_results import QuantumMachinesResult
from qililab.settings import Settings
from qililab.typings import Parameter


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

    return qmm


class MockJob:
    """Mocks a running job from Quantum Machines"""

    def __init__(self):
        self.result_handles = MockStreamingFetcher()


class MockStreamingFetcher:
    """Mocks the StreamingFetcher class from Quantum Machines."""

    def __init__(self):
        self.values = [("", MockSingleHandle()), ("", MockSingleHandle())]
        self.index = 0

    def wait_for_all_values(self):
        """Mocks waiting for all values method from streamer"""
        return MagicMock

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.values):
            result = self.values[self.index]
            self.index += 1
            return result

        raise StopIteration


class MockSingleHandle:
    """Mocks a single result handle from quantum machines results module."""

    def __init__(self):
        self.values = np.zeros((10))
        self.index = 0

    def fetch_all(self):
        """Mocks fetching all values from the result handle."""
        return self.values


class TestQMM:
    """This class contains the unit tests for the ``QMM`` class."""

    @patch("qililab.instruments.quantum_machines.qmm.QuantumMachinesManager")
    @patch("qililab.instruments.Instrument.initial_setup")
    def test_initial_setup(
        self, mock_instrument_init: MagicMock, mock_init: MagicMock, qmm: QMM
    ):  # pylint: disable=unused-argument
        """Test QMM class initialization."""
        qmm.initial_setup()
        mock_instrument_init.assert_called()

        assert isinstance(qmm.qm, MagicMock)

    def test_settings(self, qmm: QMM):
        """Test QMMSettings have been set correctly"""

        assert isinstance(qmm.settings, Settings)

    @patch("qm.QuantumMachine")
    def test_execute(self, mock_qm: MagicMock, qmm: QMM, qua_program: Program):  # pylint: disable=unused-argument
        """Test execute method"""
        mock_qm.return_value.execute.return_value = MagicMock
        qmm.qm = mock_qm
        job = qmm.run(qua_program)

        assert isinstance(job, MagicMock)

    def test_get_acquisitions(self, qmm: QMM):
        """Test get_acquisition method"""
        job = MockJob()
        result = qmm.get_acquisitions(job)

        assert isinstance(result, QuantumMachinesResult)
        assert result.array.shape == (2, 10)

    @patch("qm.QuantumMachine")
    def test_simulate(self, mock_qm: MagicMock, qmm: QMM, qua_program: Program):  # pylint: disable=unused-argument
        """Test execute method"""
        mock_qm.return_value.simulate.return_value = MagicMock
        qmm.qm = mock_qm
        job = qmm.simulate(qua_program)

        assert isinstance(job, MagicMock)

    def test_set_parameter(self, qmm: QMM):
        """Tests that set_parameter method raises a not implemented error."""
        with pytest.raises(NotImplementedError, match="Setting a parameter is not supported for Quantum Machines yet."):
            _ = qmm.set_parameter(parameter=Parameter.LO_FREQUENCY, value=0.0)
