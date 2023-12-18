"""This file tests the the ``qm_manager`` class"""
import copy
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qm import Program
from qm.qua import play, program

from qililab.instruments.quantum_machines import QuantumMachinesManager
from qililab.platform import Platform
from qililab.result.quantum_machines_results import QuantumMachinesMeasurementResult
from qililab.settings import Settings
from qililab.typings import Parameter
from tests.data import SauronQuantumMachines
from tests.test_utils import build_platform


@pytest.fixture(name="qua_program")
def fixture_qua_program():
    """Dummy QUA Program"""
    with program() as dummy_qua_program:
        play("pulse1", "element1")

    return dummy_qua_program


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=SauronQuantumMachines.runcard)


@pytest.fixture(name="qmm")
def fixture_qmm():
    """Fixture that returns an instance a qililab wrapper for Quantum Machines Manager."""
    settings = copy.deepcopy(SauronQuantumMachines.qmm)
    settings.pop("name")
    qmm = QuantumMachinesManager(settings=settings)
    qmm.device = MagicMock

    return qmm


@pytest.fixture(name="qmm_with_octave")
def fixture_qmm_with_octave():
    """Fixture that returns an instance a qililab wrapper for Quantum Machines Manager."""
    settings = copy.deepcopy(SauronQuantumMachines.qmm_with_octave)
    settings.pop("name")
    qmm = QuantumMachinesManager(settings=settings)
    qmm.device = MagicMock

    return qmm


class MockJob:
    """Mocks a running job from Quantum Machines"""

    def __init__(self):
        self.result_handles = MockStreamingFetcher()


class MockStreamingFetcher:
    """Mocks the StreamingFetcher class from Quantum Machines."""

    def __init__(self):
        self.values = [("I", MockSingleHandle()), ("Q", MockSingleHandle())]
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

    def fetch_all(self, flat_struct: bool):
        """Mocks fetching all values from the result handle."""
        return self.values


class TestQMM:
    """This class contains the unit tests for the ``QMM`` class."""

    @patch("qililab.instruments.quantum_machines.qmm.QMM")
    @patch("qililab.instruments.Instrument.initial_setup")
    @pytest.mark.parametrize("qmm_name", ["qmm", "qmm_with_octave"])
    def test_initial_setup(
        self, mock_instrument_init: MagicMock, mock_init: MagicMock, qmm_name, request
    ):  # pylint: disable=unused-argument
        """Test QMM class initialization."""
        qmm = request.getfixturevalue(qmm_name)
        qmm.initial_setup()
        mock_init.assert_called()

        assert isinstance(qmm.qmm, MagicMock)
        assert isinstance(qmm.config, dict)

    @pytest.mark.parametrize("qmm_name", ["qmm", "qmm_with_octave"])
    def test_settings(self, qmm_name, request):
        """Test QMMSettings have been set correctly"""

        qmm = request.getfixturevalue(qmm_name)
        assert isinstance(qmm.settings, Settings)

    @patch("qm.QuantumMachine")
    def test_execute(
        self, mock_qm: MagicMock, qmm: QuantumMachinesManager, qua_program: Program
    ):  # pylint: disable=unused-argument
        """Test execute method"""
        mock_qm.return_value.execute.return_value = MagicMock
        qmm.qm = mock_qm
        job = qmm.run(qua_program)

        assert isinstance(job, MagicMock)

    def test_get_acquisitions(self, qmm: QuantumMachinesManager):
        """Test get_acquisition method"""
        job = MockJob()
        results = qmm.get_acquisitions(job)

        assert isinstance(results, dict)
        assert "I" in results
        assert "Q" in results

    @patch("qm.QuantumMachine")
    def test_simulate(
        self, mock_qm: MagicMock, qmm: QuantumMachinesManager, qua_program: Program
    ):  # pylint: disable=unused-argument
        """Test execute method"""
        mock_qm.return_value.simulate.return_value = MagicMock
        qmm.qm = mock_qm
        job = qmm.simulate(qua_program)

        assert isinstance(job, MagicMock)

    def test_set_parameter(self, qmm: QuantumMachinesManager):
        """Tests that set_parameter method raises a not implemented error."""
        with pytest.raises(NotImplementedError, match="Setting a parameter is not supported for Quantum Machines yet."):
            _ = qmm.set_parameter(parameter=Parameter.LO_FREQUENCY, value=0.0)
