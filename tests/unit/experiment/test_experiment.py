"""Tests for the Experiment class."""
import copy
import os
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from qililab import build_platform
from qililab.constants import DATA, RUNCARD, SCHEMA
from qililab.execution.execution_manager import ExecutionManager
from qililab.experiment import Experiment
from qililab.platform import Platform
from qililab.result.results import Results
from qililab.result.vna_result import VNAResult
from qililab.typings import Parameter
from qililab.typings.enums import InstrumentName
from qililab.typings.experiment import ExperimentOptions
from qililab.utils import Loop
from tests.data import Galadriel, SauronVNA, experiment_params
from tests.utils import mock_instruments, platform_db


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


@pytest.fixture(name="nested_experiment", params=experiment_params)
def fixture_nested_experiment(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, _ = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="galdriel")
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
    return Experiment(platform=platform, options=options)


@pytest.fixture(name="experiment_all_platforms", params=experiment_params)
def fixture_experiment_all_platforms(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, _ = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="galadriel")
            mock_load.assert_called()
            mock_open.assert_called()
    # Build loop from an existing alias on the testing platform Galadriel
    loop = Loop(
        alias=Galadriel.buses[0][RUNCARD.ALIAS],
        parameter=Parameter.LO_FREQUENCY,
        values=np.linspace(start=3544000000, stop=3744000000, num=2),
    )
    options = ExperimentOptions(loops=[loop])
    experiment = Experiment(platform=platform, options=options)
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="experiment_reset", params=experiment_params)
def fixture_experiment_reset(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, _ = request.param  # type: ignore
    runcard = copy.deepcopy(runcard)
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
    experiment = Experiment(platform=platform, options=options)
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="exp", params=experiment_params)
def fixture_exp(request: pytest.FixtureRequest):
    """Return Experiment object."""
    runcard, _ = request.param  # type: ignore
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="galadriel")
            mock_load.assert_called()
            mock_open.assert_called()
    loop = Loop(
        alias=Galadriel.buses[0][RUNCARD.ALIAS],
        parameter=Parameter.DURATION,
        values=np.arange(start=4, stop=1000, step=40),
    )
    options = ExperimentOptions(loops=[loop])
    return Experiment(platform=platform, options=options)


@pytest.fixture(name="vna_experiment")
@patch(
    "qililab.instrument_controllers.vector_network_analyzer.keysight_E5080B_vna_controller.E5080BDriver",
    autospec=True,
)
@patch(
    "qililab.instrument_controllers.vector_network_analyzer.agilent_E5071B_vna_controller.VectorNetworkAnalyzerDriver",
    autospec=True,
)
def fixture_vna_experiment(mock_agilent: MagicMock, mock_keysight: MagicMock, sauron_platform: Platform):
    """Return a connected experiment with the VNA instrument"""
    loop = Loop(
        alias=SauronVNA.buses[0][RUNCARD.ALIAS],
        parameter=Parameter.POWER,
        values=np.linspace(0, 10, 10),
    )
    options = ExperimentOptions(loops=[loop])
    vna_experiment = Experiment(platform=sauron_platform, options=options)
    vna_experiment.connect()
    return vna_experiment


@pytest.fixture(name="sauron_platform")
def fixture_sauron_platform() -> Platform:
    """Return Platform object."""
    return platform_db(runcard=SauronVNA.runcard)


class TestAttributes:
    """Unit tests checking the Experiment attributes and methods"""

    def test_platform_attributes(self, exp: Experiment):
        """Test platform attributes after initialization."""
        assert isinstance(exp.platform, Platform)
        assert isinstance(exp.options, ExperimentOptions)
        assert not hasattr(exp, "execution_manager")
        assert not hasattr(exp, "results")
        assert not hasattr(exp, "results_path")
        assert not hasattr(exp, "_plot")
        assert not hasattr(exp, "_remote_id")


class TestProperties:
    """Test the properties of the Experiment class."""

    def test_software_average_property(self, exp: Experiment):
        """Test software_average property."""
        assert exp.software_average == exp.options.settings.software_average

    def test_hardware_average_property(self, exp: Experiment):
        """Test hardware_average property."""
        assert exp.hardware_average == exp.options.settings.hardware_average

    def test_repetition_duration_property(self, exp: Experiment):
        """Test repetition_duration property."""
        assert exp.repetition_duration == exp.options.settings.repetition_duration


class TestMethods:
    """Test the methods of the Experiment class."""

    def test_connect(self, experiment_all_platforms: Experiment):
        """Test the ``connect`` method of the Experiment class."""
        with patch("qililab.platform.platform.Platform.connect") as mock_connect:
            experiment_all_platforms.connect()
            mock_connect.assert_called_once()

    def test_initial_setup(self, experiment_all_platforms: Experiment):
        """Test the ``initial_setup`` method of the Experiment class."""
        with patch("qililab.platform.platform.Platform.initial_setup") as mock_initial_setup:
            experiment_all_platforms.initial_setup()
            mock_initial_setup.assert_called_once()

    def test_build_execution(self, exp: Experiment):
        """Test the ``build_execution`` method of the Experiment class."""
        # Check that attributes don't exist
        assert not hasattr(exp, "execution_manager")
        assert not hasattr(exp, "results")
        assert not hasattr(exp, "results_path")
        assert not hasattr(exp, "_plot")
        assert not hasattr(exp, "_remote_id")
        exp.build_execution()
        # Check that new attributes are created
        assert isinstance(exp.execution_manager, ExecutionManager)
        assert not hasattr(exp, "results")
        assert not hasattr(exp, "results_path")
        assert not hasattr(exp, "_plot")
        assert not hasattr(exp, "_remote_id")

    def test_run_without_data_path_raises_error(self, exp: Experiment):
        """Test that the ``build_execution`` method of the ``Experiment`` class raises an error when no DATA
        path is specified."""
        old_data = os.environ.get(DATA)
        del os.environ[DATA]
        with pytest.raises(ValueError, match="Environment variable DATA is not set"):
            exp.build_execution()
            exp.run()
        if old_data is not None:
            os.environ[DATA] = old_data

    def test_run_with_vna_result(self, vna_experiment: Experiment):
        """Test the ``run`` method of the Experiment class, this is a temporary test until ``run``function of the vna is implemented."""
        vna_experiment.build_execution()
        vna_experiment.platform.connection = MagicMock()  # mock connection
        assert not hasattr(vna_experiment, "_plot")
        assert not hasattr(vna_experiment, "results")
        with patch("qililab.experiment.experiment.open") as mock_open:
            with patch("qililab.experiment.experiment.os.makedirs") as mock_makedirs:
                with patch("qililab.experiment.experiment.LivePlot") as mock_plot:
                    with patch("qililab.execution.execution_manager.BusExecution.acquire_result") as mock_acq_res:
                        mock_acq_res.return_value = VNAResult(i=np.array([1, 2]), q=np.array([3, 4]))
                        # Build execution
                        results = vna_experiment.run()
                        # Assert that the mocks are called when building the execution (such that NO files are created)
                        mock_open.assert_called()
                        mock_makedirs.assert_called()
                        mock_plot.assert_called_once_with(
                            connection=vna_experiment.platform.connection,
                            loops=vna_experiment.options.loops or [],
                            num_schedules=1,
                            title=vna_experiment.options.name,
                        )
                        mock_plot.assert_called_once()
                        assert isinstance(results, Results)
                        assert results.results[0] == mock_acq_res.return_value
        assert len(vna_experiment.results.results) > 0

    @patch("qililab.experiment.experiment.Experiment.remote_save_experiment", autospec=True)
    def test_run_with_vna_result_remote_svaing(self, mock_remote_save: MagicMock, vna_experiment: Experiment):
        """Test the ``run`` method of the Experiment class, this is a temporary test until ``run``function of the vna is implemented."""
        vna_experiment.options.remote_save = True
        vna_experiment.build_execution()
        vna_experiment.platform.connection = MagicMock()  # mock connection
        assert not hasattr(vna_experiment, "_plot")
        assert not hasattr(vna_experiment, "results")
        with patch("qililab.experiment.experiment.open") as mock_open:
            with patch("qililab.experiment.experiment.os.makedirs") as mock_makedirs:
                with patch("qililab.experiment.experiment.LivePlot") as mock_plot:
                    with patch("qililab.execution.execution_manager.BusExecution.acquire_result") as mock_acq_res:
                        with patch(
                            "qililab.experiment.experiment.Experiment.remote_save_experiment"
                        ) as mock_remote_save:
                            mock_acq_res.return_value = VNAResult(i=np.array([1, 2]), q=np.array([3, 4]))
                            # Build execution
                            results = vna_experiment.run()
                            # Assert that the mocks are called when building the execution (such that NO files are created)
                            mock_remote_save.assert_called()
                            mock_open.assert_called()
                            mock_makedirs.assert_called()
                            mock_plot.assert_called_once_with(
                                connection=vna_experiment.platform.connection,
                                loops=vna_experiment.options.loops or [],
                                num_schedules=1,
                                title=vna_experiment.options.name,
                            )
                            mock_plot.assert_called_once()
                            assert isinstance(results, Results)
                            assert results.results[0] == mock_acq_res.return_value
                            mock_remote_save.assert_called()
        assert len(vna_experiment.results.results) > 0

    @patch("qililab.execution.execution_manager.BusExecution.acquire_result")
    def test_run_builds_execution_manager_if_not_exists(self, mock_acq_res: MagicMock, vna_experiment: Experiment):
        """Test that the ``run`` method builds the execution if ``execution_manager`` was not created."""
        assert not hasattr(vna_experiment, "execution_manager")
        with patch("qililab.experiment.experiment.open") as _:
            with patch("qililab.experiment.experiment.os.makedirs") as _:
                with patch("qililab.experiment.experiment.LivePlot") as _:
                    mock_acq_res.return_value = VNAResult(i=np.array([1, 2]), q=np.array([3, 4]))
                    vna_experiment.run()
        assert hasattr(vna_experiment, "execution_manager")

    def test_turn_on_instruments(self, connected_experiment: Experiment):
        """Test the ``turn_on_instruments`` method of the Experiment class."""
        connected_experiment.build_execution()
        with patch("qililab.platform.platform.Platform.turn_on_instruments") as mock_turn_on:
            connected_experiment.turn_on_instruments()
            mock_turn_on.assert_called_once()

    def test_turn_on_instruments_raises_error(self, exp: Experiment):
        """Test that the ``turn_on_instruments`` method raises an error if ``build_execution`` has not been called."""
        with pytest.raises(ValueError, match="Please build the execution_manager before turning on the instruments"):
            exp.turn_on_instruments()

    def test_turn_off_instruments(self, connected_experiment: Experiment):
        """Test the ``turn_off_instruments`` method of the Experiment class."""
        connected_experiment.build_execution()
        with patch("qililab.platform.platform.Platform.turn_off_instruments") as mock_turn_off:
            connected_experiment.turn_off_instruments()
            mock_turn_off.assert_called_once()

    def test_turn_off_instruments_raises_error(self, exp: Experiment):
        """Test that the ``turn_off_instruments`` method raises an error if ``build_execution`` has not been called."""
        with pytest.raises(ValueError, match="Please build the execution_manager before turning off the instruments"):
            exp.turn_off_instruments()

    def test_disconnect(self, exp: Experiment):
        """Test the ``disconnect`` method of the Experiment class."""
        with patch("qililab.platform.platform.Platform.disconnect") as mock_disconnect:
            exp.disconnect()
            mock_disconnect.assert_called_once()

    def test_to_dict_method(self, experiment_all_platforms: Experiment):
        """Test to_dict method."""
        dictionary = experiment_all_platforms.to_dict()
        assert isinstance(dictionary, dict)

    def test_from_dict_method(self, exp: Experiment):
        # sourcery skip: class-extract-method
        """Test from_dict method."""
        dictionary = exp.to_dict()
        experiment_2 = Experiment.from_dict(dictionary)
        assert isinstance(experiment_2, Experiment)

    def test_from_dict_method_loop(self, nested_experiment: Experiment):
        """Test from_dict method with an experiment with a nested loop."""
        dictionary = nested_experiment.to_dict()
        experiment_2 = Experiment.from_dict(dictionary)
        assert isinstance(experiment_2, Experiment)

    def test_loop_num_loops_property(self, experiment_all_platforms: Experiment):
        """Test loop's num_loops property."""
        if experiment_all_platforms.options.loops is not None:
            print(experiment_all_platforms.options.loops[0].num_loops)

    def test_str_method(self, experiment_all_platforms: Experiment):
        """Test __str__ method."""
        expected = f"Experiment {experiment_all_platforms.options.name}:\n{str(experiment_all_platforms.platform)}\n{str(experiment_all_platforms.options)}"
        test_str = str(experiment_all_platforms)
        assert expected == test_str

    def test_filter_loops_values_with_external_parameters_raises_exception(self, exp: Experiment):
        """Test _filter_loops_values_with_external_paramters raises an exception when lists of values and loops have not the same length"""
        values = (1.5, -1.5)
        loops = [Loop(alias="foo", parameter=Parameter.POWER, values=np.linspace(0, 10, 1))]
        with pytest.raises(
            ValueError, match=f"Values list length: {len(values)} differ from loops list length: {len(loops)}."
        ):
            exp._filter_loops_values_with_external_parameters(values, loops)

    def test_filter_loops_values_with_external_parameters_pops(self, exp: Experiment):
        """Test _filter_loops_values_with_external_paramters returns a list of the original values and loops without the ones containing external parameters"""
        test_value = (1.5,)
        test_loop = [
            Loop(
                alias=Galadriel.buses[0][RUNCARD.ALIAS],
                parameter=Parameter.EXTERNAL,
                values=np.linspace(start=0, stop=10, num=1),
            )
        ]
        filtered_loops, filtered_values = exp._filter_loops_values_with_external_parameters(test_value, test_loop)
        assert filtered_loops == []
        assert filtered_values == []

    def test_prepare_results_returns_no_path(self, exp: Experiment):
        """Test the prepare_results method with save_results=False returns no results_path"""
        exp.build_execution()
        _, results_path = exp.prepare_results(save_results=False)
        assert results_path is None


class TestSetParameter:
    """Unit tests for the ``set_parameter`` method."""

    def test_set_parameter_method_without_a_connected_device(self, exp: Experiment):
        """Test set_parameter method raising an error when device is not connected."""
        with pytest.raises(ValueError):
            exp.set_parameter(alias=InstrumentName.QBLOX_QCM.value, parameter=Parameter.IF, value=1e9, channel_id=0)

    @patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
    @patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
    @patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
    @patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
    def test_set_parameter_method_with_a_connected_device(
        self,
        mock_urllib: MagicMock,
        mock_keithley: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        exp: Experiment,  # pylint: disable=unused-argument
    ):
        """Test set_parameter method."""
        # add dynamically created attributes
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        exp.platform.connect()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        exp.set_parameter(alias=InstrumentName.QBLOX_QCM.value, parameter=Parameter.IF, value=1e9, channel_id=0)

    def test_set_parameter_method_with_platform_settings(self, exp: Experiment):
        """Test set_parameter method with platform settings."""
        exp.set_parameter(alias="M(0)", parameter=Parameter.AMPLITUDE, value=0.3)
        assert exp.platform.settings.get_gate(name="M", qubits=0).amplitude == 0.3

    def test_set_parameter_method_with_instrument_controller_reset(self, exp: Experiment):
        """Test set_parameter method with instrument controller reset."""
        exp.set_parameter(alias="pulsar_controller_qcm_0", parameter=Parameter.RESET, value=False)
        assert (
            exp.platform.instrument_controllers.get_instrument_controller(
                alias="pulsar_controller_qcm_0"
            ).settings.reset
            is False
        )


class TestReset:
    """Unit tests for the reset option."""

    @patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
    @patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
    @patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
    @patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
    @patch("qililab.instrument_controllers.instrument_controller.InstrumentController.reset")
    def test_set_reset_true_with_connected_device(
        self,
        mock_reset: MagicMock,
        mock_urllib: MagicMock,  # pylint: disable=unused-argument
        mock_keithley: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        exp: Experiment,  # pylint: disable=unused-argument
    ):
        """Test set reset to false method."""
        # add dynamically created attributes
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        exp.platform.connect()
        exp.platform.disconnect()
        mock_reset.assert_called()
        assert mock_reset.call_count == 12

    @patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
    @patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
    @patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
    @patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
    @patch("qililab.instrument_controllers.instrument_controller.InstrumentController.reset")
    def test_set_reset_false_with_connected_device(
        self,
        mock_reset: MagicMock,
        mock_urllib: MagicMock,  # pylint: disable=unused-argument
        mock_keithley: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        experiment_reset: Experiment,  # pylint: disable=unused-argument
    ):
        """Test set reset to false method."""
        # add dynamically created attributes
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        experiment_reset.platform.connect()
        experiment_reset.platform.disconnect()
        assert mock_reset.call_count == 10
