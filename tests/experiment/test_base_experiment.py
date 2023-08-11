"""Tests for the BaseExperiment class."""
import copy
import os
from queue import Queue
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import qililab as ql
from qililab.constants import DATA, RUNCARD
from qililab.execution.execution_manager import ExecutionManager
from qililab.experiment.base_experiment import BaseExperiment
from qililab.platform import Platform
from qililab.typings import Parameter
from qililab.typings.enums import InstrumentName
from qililab.typings.experiment import ExperimentOptions
from qililab.utils import Loop
from tests.data import Galadriel, SauronVNA, experiment_params
from tests.test_utils import build_platform, mock_instruments


class MockExperiment(BaseExperiment):
    @classmethod
    def from_dict(cls, dictionary: dict):
        pass

    def _execute_recursive_loops(self, loops: list[Loop] | None, queue: Queue, depth=0):
        pass


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
    experiment_all_platforms: BaseExperiment,
):
    """Fixture that mocks all the instruments, connects to the mocked instruments and returns the `BaseExperiment`
    instance."""
    mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
    experiment_all_platforms.platform.connect()
    mock_mini_circuits.assert_called()
    mock_keithley.assert_called()
    mock_rs.assert_called()
    mock_pulsar.assert_called()
    return experiment_all_platforms


@pytest.fixture(name="connected_nested_experiment")
@patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
@patch("qililab.instrument_controllers.rohde_schwarz.sgs100a_controller.RohdeSchwarzSGS100A", autospec=True)
@patch("qililab.instrument_controllers.keithley.keithley_2600_controller.Keithley2600Driver", autospec=True)
@patch("qililab.instrument_controllers.mini_circuits.mini_circuits_controller.MiniCircuitsDriver", autospec=True)
def fixture_connected_nested_experiment(
    mock_mini_circuits: MagicMock,
    mock_keithley: MagicMock,
    mock_rs: MagicMock,
    mock_pulsar: MagicMock,
    nested_experiment: BaseExperiment,
):
    """Fixture that mocks all the instruments, connects to the mocked instruments and returns the `BaseExperiment`
    instance."""
    mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
    nested_experiment.platform.connect()
    mock_mini_circuits.assert_called()
    mock_keithley.assert_called()
    mock_rs.assert_called()
    mock_pulsar.assert_called()
    return nested_experiment


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=Galadriel.runcard)


@pytest.fixture(name="sauron_platform")
def fixture_sauron_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=SauronVNA.runcard)


@pytest.fixture(name="nested_experiment", params=experiment_params)
def fixture_nested_experiment(request: pytest.FixtureRequest):
    """Return BaseExperiment object."""
    runcard, _ = request.param  # type: ignore
    platform = build_platform(runcard)
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
    return MockExperiment(platform=platform, options=options)


@pytest.fixture(name="experiment_all_platforms", params=experiment_params)
def fixture_experiment_all_platforms(request: pytest.FixtureRequest):
    """Return BaseExperiment object."""
    runcard, _ = request.param  # type: ignore
    platform = build_platform(runcard)
    # Build loop from an existing alias on the testing platform
    loop = Loop(
        alias=Galadriel.buses[0][RUNCARD.ALIAS],  # type: ignore
        parameter=Parameter.LO_FREQUENCY,
        values=np.linspace(start=3544000000, stop=3744000000, num=2),
    )
    options = ExperimentOptions(loops=[loop])
    experiment = MockExperiment(platform=platform, options=options)
    return experiment


@pytest.fixture(name="experiment_reset", params=experiment_params)
def fixture_experiment_reset(request: pytest.FixtureRequest):
    """Return BaseExperiment object."""
    runcard, _ = request.param  # type: ignore
    runcard = copy.deepcopy(runcard)
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            mock_load.return_value[RUNCARD.INSTRUMENT_CONTROLLERS][0] |= {"reset": False}
            platform = ql.build_platform(name="sauron")
            mock_load.assert_called()
            mock_open.assert_called()
    loop = Loop(
        alias="rs_0",
        parameter=Parameter.LO_FREQUENCY,
        values=np.linspace(start=3544000000, stop=3744000000, num=2),
    )
    options = ExperimentOptions(loops=[loop])
    experiment = MockExperiment(platform=platform, options=options)
    mock_load.assert_called()
    return experiment


@pytest.fixture(name="exp", params=experiment_params)
def fixture_exp(request: pytest.FixtureRequest):
    """Return BaseExperiment object."""
    runcard, _ = request.param  # type: ignore
    platform = build_platform(runcard)
    loop = Loop(
        alias=Galadriel.buses[0][RUNCARD.ALIAS],  # type: ignore
        parameter=Parameter.DURATION,
        values=np.arange(start=4, stop=1000, step=40),
    )
    options = ExperimentOptions(loops=[loop])
    return MockExperiment(platform=platform, options=options)


class TestAttributes:
    """Unit tests checking the BaseExperiment attributes and methods"""

    def test_platform_attributes(self, exp: BaseExperiment):
        """Test platform attributes after initialization."""
        assert isinstance(exp.platform, Platform)
        assert isinstance(exp.options, ExperimentOptions)
        assert not hasattr(exp, "execution_manager")
        assert not hasattr(exp, "results")
        assert not hasattr(exp, "results_path")
        assert not hasattr(exp, "_plot")
        assert not hasattr(exp, "_remote_id")


class TestProperties:
    """Test the properties of the BaseExperiment class."""

    def test_software_average_property(self, exp: BaseExperiment):
        """Test software_average property."""
        assert exp.software_average == exp.options.settings.software_average

    def test_hardware_average_property(self, exp: BaseExperiment):
        """Test hardware_average property."""
        assert exp.hardware_average == exp.options.settings.hardware_average

    def test_repetition_duration_property(self, exp: BaseExperiment):
        """Test repetition_duration property."""
        assert exp.repetition_duration == exp.options.settings.repetition_duration


class TestMethods:
    """Test the methods of the BaseExperiment class."""

    def test_build_execution(self, exp: BaseExperiment):
        """Test the ``build_execution`` method of the BaseExperiment class."""
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

    def test_run_without_data_path_raises_error(self, exp: BaseExperiment):
        """Test that the ``build_execution`` method of the ``BaseExperiment`` class raises an error when no DATA
        path is specified."""
        old_data = os.environ.get(DATA)
        del os.environ[DATA]
        with pytest.raises(ValueError, match="Environment variable DATA is not set"):
            exp.build_execution()
            exp.run()
        if old_data is not None:
            os.environ[DATA] = old_data

    def test_run_raises_error(self, exp: BaseExperiment):
        """Test that the ``run`` method raises an error if ``build_execution`` has not been called."""
        with pytest.raises(ValueError, match="Please build the execution_manager before running an experiment"):
            exp.run()

    def test_to_dict_method(self, experiment_all_platforms: BaseExperiment):
        """Test to_dict method."""
        dictionary = experiment_all_platforms.to_dict()
        assert isinstance(dictionary, dict)

    def test_loop_num_loops_property(self, experiment_all_platforms: BaseExperiment):
        """Test loop's num_loops property."""
        if experiment_all_platforms.options.loops is not None:
            assert isinstance(experiment_all_platforms.options.loops[0].num_loops, int)
            assert isinstance(str(experiment_all_platforms.options.loops[0].num_loops), str)

    def test_str_method(self, experiment_all_platforms: BaseExperiment):
        """Test __str__ method."""
        expected = f"BaseExperiment {experiment_all_platforms.options.name}:\n{str(experiment_all_platforms.platform)}\n{str(experiment_all_platforms.options)}"
        test_str = str(experiment_all_platforms)
        assert expected == test_str

    def test_filter_loops_values_with_external_parameters_raises_exception(self, exp: BaseExperiment):
        """Test _filter_loops_values_with_external_paramters raises an exception when lists of values and loops have not the same length"""
        values = (1.5, -1.5)
        loops = [Loop(alias="foo", parameter=Parameter.POWER, values=np.linspace(0, 10, 1))]
        with pytest.raises(
            ValueError, match=f"Values list length: {len(values)} differ from loops list length: {len(loops)}."
        ):
            exp._filter_loops_values_with_external_parameters(values, loops)

    def test_filter_loops_values_with_external_parameters_pops(self, exp: BaseExperiment):
        """Test _filter_loops_values_with_external_paramters returns a list of the original values and loops without the ones containing external parameters"""
        test_value = (1.5,)
        test_loop = [
            Loop(
                alias=Galadriel.buses[0][RUNCARD.ALIAS],  # type: ignore
                parameter=Parameter.EXTERNAL,
                values=np.linspace(start=0, stop=10, num=1),
            )
        ]
        filtered_loops, filtered_values = exp._filter_loops_values_with_external_parameters(test_value, test_loop)
        assert filtered_loops == []
        assert filtered_values == []

    def test_prepare_results_returns_no_path(self, exp: BaseExperiment):
        """Test the prepare_results method with save_results=False returns no results_path"""
        exp.build_execution()
        _, results_path = exp.prepare_results(save_experiment=False, save_results=False)
        assert results_path is None


class TestSetParameter:
    """Unit tests for the ``set_parameter`` method."""

    def test_set_parameter_method_without_a_connected_device(self, exp: BaseExperiment):
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
        exp: BaseExperiment,  # pylint: disable=unused-argument
    ):
        """Test set_parameter method."""
        # add dynamically created attributes
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        exp.platform.connect()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        exp.set_parameter(alias=InstrumentName.QBLOX_QCM.value, parameter=Parameter.IF, value=1e9, channel_id=0)

    def test_set_parameter_method_with_platform_gate_settings(self, exp: BaseExperiment):
        """Test set_parameter method with platform gate settings."""
        exp.set_parameter(alias="M(0)_0", parameter=Parameter.AMPLITUDE, value=0.3)
        assert exp.platform.gate_settings.get_gate(name="M", qubits=0)[0].pulse.amplitude == 0.3

    def test_set_parameter_method_with_instrument_controller_reset(self, exp: BaseExperiment):
        """Test set_parameter method with instrument controller reset."""
        exp.set_parameter(alias="pulsar_controller_qcm_0", parameter=Parameter.RESET, value=False)
        assert (
            exp.platform.instrument_controllers.get_instrument_controller(
                alias="pulsar_controller_qcm_0"
            ).settings.reset
            is False
        )

    def test_set_parameter_method_with_delay(self, exp: BaseExperiment):
        """Test set_parameter method with delay parameter."""
        bus_delay = 0
        exp.build_execution = MagicMock()  # type: ignore
        alias = Galadriel.buses[0][RUNCARD.ALIAS]
        element = exp.platform.get_element(alias)  # type: ignore
        exp.set_parameter(element=element, alias=alias, parameter=Parameter.DELAY, value=bus_delay)  # type: ignore
        assert exp.platform.get_bus_by_alias(alias).delay == bus_delay  # type: ignore
        exp.build_execution.assert_called_once_with()


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
        exp: BaseExperiment,  # pylint: disable=unused-argument
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
        experiment_reset: BaseExperiment,  # pylint: disable=unused-argument
    ):
        """Test set reset to false method."""
        # add dynamically created attributes
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar, mock_keithley=mock_keithley)
        experiment_reset.platform.connect()
        experiment_reset.platform.disconnect()
        assert mock_reset.call_count == 10
