"""Tests for the Experiment class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qibo.models.circuit import Circuit

from qililab import build_platform
from qililab.constants import RUNCARD, SCHEMA
from qililab.execution import ExecutionManager
from qililab.experiment import Experiment
from qililab.platform import Platform
from qililab.pulse import PulseSchedule
from qililab.typings import Parameter
from qililab.typings.experiment import ExperimentOptions
from qililab.utils import Loop
from tests.data import experiment_params, simulated_experiment_circuit
from tests.utils import mock_instruments


@pytest.fixture(name="connected_experiment")
@patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
@patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
@patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
@patch("qililab.instrument_controllers.mini_circuits.mini_circuits_controller.MiniCircuitsDriver", autospec=True)
def fixture_connected_experiment(
    mock_mini_circuits: MagicMock,
    mock_keithley: MagicMock,
    mock_rs: MagicMock,
    mock_pulsar: MagicMock,
    experiment_all_platforms: Experiment,
):
    """Fixture that mocks all the instruments, connects to the mocked instruments and returns the `Experiment`
    instance."""
    mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
    experiment_all_platforms.connect()
    mock_mini_circuits.assert_called()
    mock_keithley.assert_called()
    mock_rs.assert_called()
    mock_pulsar.assert_called()
    return experiment_all_platforms


class TestMethods:
    """Test the methods of the Experiment class."""

    def test_build_execution(self, experiment: Experiment):
        """Test the ``build_execution`` method of the Experiment class."""
        # Check that the ``pulse_schedules`` attribute is empty
        assert len(experiment.pulse_schedules) == 0
        # Check that attributes don't exist
        assert not hasattr(experiment, "execution_manager")
        assert not hasattr(experiment, "results")
        assert not hasattr(experiment, "results_path")
        assert not hasattr(experiment, "_plot")
        assert not hasattr(experiment, "_remote_id")
        experiment.build_execution()
        # Check that the ``pulse_schedules`` attribute is NOT empty
        assert len(experiment.pulse_schedules) == len(experiment.circuits)
        # Check that new attributes are created
        assert isinstance(experiment.execution_manager, ExecutionManager)
        assert not hasattr(experiment, "results")
        assert not hasattr(experiment, "results_path")
        assert not hasattr(experiment, "_plot")
        assert not hasattr(experiment, "_remote_id")


class TestAttributes:
    """Unit tests checking the Experiment attributes and methods"""

    def test_platform_attributes(self, experiment: Experiment):
        """Test platform attributes after initialization."""
        assert isinstance(experiment.platform, Platform)
        assert isinstance(experiment.circuits, list)
        if len(experiment.circuits) > 0:
            for circuit in experiment.circuits:
                assert isinstance(circuit, Circuit)
        assert isinstance(experiment.pulse_schedules, list)
        if len(experiment.pulse_schedules) > 0:
            for pulse_schedule in experiment.pulse_schedules:
                assert isinstance(pulse_schedule, PulseSchedule)
        assert isinstance(experiment.options, ExperimentOptions)
        assert not hasattr(experiment, "execution_manager")
        assert not hasattr(experiment, "results")
        assert not hasattr(experiment, "results_path")
        assert not hasattr(experiment, "_plot")
        assert not hasattr(experiment, "_remote_id")


@pytest.fixture(name="experiment_reset", params=experiment_params)
def fixture_experiment_reset(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            mock_load.return_value[RUNCARD.SCHEMA][SCHEMA.INSTRUMENT_CONTROLLERS][0] |= {"reset": False}
            platform = build_platform(name="sauron")
            mock_load.assert_called()
            mock_open.assert_called()
    loop = Loop(
        alias="rs_0",
        parameter=Parameter.LO_FREQUENCY,
        values=np.linspace(start=3544000000, stop=3744000000, num=2),
    )
    options = ExperimentOptions(loops=[loop])
    experiment = Experiment(
        platform=platform, circuits=circuits if isinstance(circuits, list) else [circuits], options=options
    )
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="experiment_all_platforms", params=experiment_params)
def fixture_experiment_all_platforms(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, circuits = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="flux_qubit")
            mock_load.assert_called()
            mock_open.assert_called()
    experiment = Experiment(platform=platform, circuits=circuits if isinstance(circuits, list) else [circuits])
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="simulated_experiment")
def fixture_simulated_experiment(simulated_platform: Platform):
    """Return Experiment object."""
    return Experiment(platform=simulated_platform, circuits=[simulated_experiment_circuit])
