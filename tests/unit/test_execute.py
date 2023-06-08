"""Tests for the Experiment class."""
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from qililab import build_platform
from qililab.constants import DATA, RUNCARD, SCHEMA
from qililab.execution.execution_manager import ExecutionManager
from qililab.experiment import Experiment
from qililab.platform import Platform
from qililab.typings import Parameter
from qililab.typings.enums import InstrumentName
from qililab.typings.experiment import ExperimentOptions
from qililab.utils import Loop
from tests.data import FluxQubitSimulator, Galadriel, experiment_params, simulated_experiment_circuit
from tests.utils import platform_db


@pytest.fixture(name="simulated_platform")
@patch("qililab.system_control.simulated_system_control.Evolution", autospec=True)
def fixture_simulated_platform(mock_evolution: MagicMock) -> Platform:
    """Return Platform object."""

    # Mocked Evolution needs: system.qubit.frequency, psi0, states, times
    mock_system = MagicMock()
    mock_system.qubit.frequency = 0
    mock_evolution.return_value.system = mock_system
    mock_evolution.return_value.states = []
    mock_evolution.return_value.times = []
    mock_evolution.return_value.psi0 = None

    with patch(
        "qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=FluxQubitSimulator.runcard
    ) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    return platform


@pytest.fixture(name="nested_experiment", params=experiment_params)
def fixture_nested_experiment(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="sauron")
            mock_load.assert_called()
            mock_open.assert_called()
    loop2 = Loop(
        alias="platform",
        parameter=Parameter.DELAY_BEFORE_READOUT,
        values=np.arange(start=40, stop=100, step=40),
    )
    loop = Loop(
        alias=InstrumentName.QBLOX_QRM.value,
        parameter=Parameter.GAIN,
        values=np.linspace(start=0, stop=1, num=2),
        channel_id=0,
        loop=loop2,
    )
    options = ExperimentOptions(loops=[loop])
    return Experiment(
        platform=platform, circuits=circuits if isinstance(circuits, list) else [circuits], options=options
    )


@pytest.fixture(name="experiment", params=experiment_params)
def fixture_experiment(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="sauron")
            mock_load.assert_called()
            mock_open.assert_called()
    loop = Loop(
        alias="X(0)",
        parameter=Parameter.DURATION,
        values=np.arange(start=4, stop=1000, step=40),
    )
    options = ExperimentOptions(loops=[loop])
    return Experiment(
        platform=platform, circuits=circuits if isinstance(circuits, list) else [circuits], options=options
    )


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return platform_db(runcard=Galadriel.runcard)

@pytest.fixture(name="simulated_experiment")
def fixture_simulated_experiment(simulated_platform: Platform):
    """Return Experiment object."""
    return Experiment(platform=simulated_platform, circuits=[simulated_experiment_circuit])


@patch("qililab.experiment.experiment.open")
@patch("qililab.experiment.experiment.yaml.safe_dump")
@patch("qililab.system_control.simulated_system_control.SimulatedSystemControl.run")
@patch("qililab.experiment.experiment.os.makedirs")
class TestSimulatedExecution:
    """Unit tests checking the execution of a simulated platform"""

    def test_execute(
        self,
        mock_open: MagicMock,
        mock_dump: MagicMock,
        mock_ssc_run: MagicMock,
        mock_makedirs: MagicMock,
        simulated_experiment: Experiment,
    ):
        """Test execute method with simulated qubit"""

        # Method under test
        results = simulated_experiment.execute()

        time.sleep(0.3)

        # Assert simulator called
        mock_ssc_run.assert_called()

        # Assert called functions
        mock_makedirs.assert_called()
        mock_open.assert_called()
        mock_dump.assert_called()

        # Test result
        with pytest.raises(ValueError):  # Result should be SimulatedResult
            results.acquisitions()
