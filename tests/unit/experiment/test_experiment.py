"""Tests for the Experiment class."""
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qcodes.instrument_drivers.tektronix.Keithley_2600_channels import KeithleyChannel
from qibo.core.circuit import Circuit
from qibo.gates import M
from qiboconnection.api import API

from qililab.execution import Execution
from qililab.experiment import Experiment
from qililab.platform import Platform
from qililab.result import Results
from qililab.typings import Instrument, Parameter

from ...conftest import mock_instruments


class TestExperiment:
    """Unit tests checking the Experiment attributes and methods"""

    def test_platform_attribute_instance(self, experiment: Experiment):
        """Test platform attribute instance."""
        assert isinstance(experiment.platform, Platform)

    def test_execution_attribute_instance(self, experiment: Experiment):
        """Test execution attribute instance."""
        assert isinstance(experiment.execution, Execution)

    def test_parameters_property(self, experiment: Experiment):
        """Test parameters property."""
        assert isinstance(experiment.parameters, str)

    def test_software_average_property(self, experiment: Experiment):
        """Test software_average property."""
        assert experiment.software_average == experiment.settings.software_average

    def test_hardware_average_property(self, experiment: Experiment):
        """Test hardware_average property."""
        assert experiment.hardware_average == experiment.settings.hardware_average

    def test_repetition_duration_property(self, experiment: Experiment):
        """Test repetition_duration property."""
        assert experiment.repetition_duration == experiment.settings.repetition_duration

    def test_to_dict_method(self, experiment_all_platforms: Experiment):
        """Test to_dict method."""
        dictionary = experiment_all_platforms.to_dict()
        assert isinstance(dictionary, dict)

    def test_from_dict_method(self, experiment: Experiment):
        # sourcery skip: class-extract-method
        """Test from_dict method."""
        dictionary = experiment.to_dict()
        experiment_2 = Experiment.from_dict(dictionary)
        assert isinstance(experiment_2, Experiment)

    def test_from_dict_method_loop(self, nested_experiment: Experiment):
        """Test from_dict method with an experiment with a nested loop."""
        dictionary = nested_experiment.to_dict()
        experiment_2 = Experiment.from_dict(dictionary)
        assert isinstance(experiment_2, Experiment)

    def test_draw_method(self, experiment_all_platforms: Experiment):
        """Test draw metho."""
        experiment_all_platforms.draw()

    def test_loop_num_loops_property(self, experiment_all_platforms: Experiment):
        """Test loop's num_loops property."""
        if experiment_all_platforms.loop is not None:
            print(experiment_all_platforms.loop.num_loops)

    def test_draw_method_with_one_bus(self, platform: Platform):
        """Test draw method with only one measurement gate."""
        circuit = Circuit(1)
        circuit.add(M(0))
        experiment = Experiment(sequences=circuit, platform=platform)
        experiment.draw()

    def test_str_method(self, experiment_all_platforms: Experiment):
        """Test __str__ method."""
        str(experiment_all_platforms)
        str(experiment_all_platforms.settings)

    def test_set_parameter_method_without_a_connected_device(self, experiment: Experiment):
        """Test set_parameter method raising an error when device is not connected."""
        with pytest.raises(AttributeError):
            experiment.set_parameter(instrument=Instrument.AWG, id_=0, parameter=Parameter.FREQUENCY, value=1e9)

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
        experiment: Experiment,  # pylint: disable=unused-argument
    ):
        """Test set_parameter method."""
        # add dynamically created attributes
        mock_instance = mock_pulsar.return_value
        mock_instance.mock_add_spec(
            [
                "reference_source",
                "sequencer0",
                "scope_acq_trigger_mode_path0",
                "scope_acq_trigger_mode_path1",
                "scope_acq_sequencer_select",
                "scope_acq_avg_mode_en_path0",
                "scope_acq_avg_mode_en_path1",
            ]
        )
        mock_instance.sequencers = [mock_instance.sequencer0, mock_instance.sequencer0]
        mock_instance.sequencer0.mock_add_spec(
            [
                "sync_en",
                "gain_awg_path0",
                "gain_awg_path1",
                "sequence",
                "mod_en_awg",
                "nco_freq",
                "scope_acq_sequencer_select",
                "channel_map_path0_out0_en",
                "channel_map_path1_out1_en",
                "demod_en_acq",
                "integration_length_acq",
                "set",
                "offset_awg_path0",
                "offset_awg_path1",
            ]
        )
        mock_instance = mock_rs.return_value
        mock_instance.mock_add_spec(["power", "frequency"])
        mock_instance = mock_keithley.return_value
        mock_instance.smua = MagicMock(KeithleyChannel)
        mock_instance.smua.mock_add_spec(["limiti", "limitv", "doFastSweep"])
        experiment.platform.connect()
        experiment.set_parameter(instrument=Instrument.AWG, id_=0, parameter=Parameter.FREQUENCY, value=1e9)

    def test_set_parameter_method_with_platform_settings(self, experiment: Experiment):
        """Test set_parameter method with platform settings."""
        experiment.set_parameter(alias="M", parameter=Parameter.AMPLITUDE, value=0.3)
        assert experiment.platform.settings.get_gate(name="M").amplitude == 0.3


@patch("qililab.instruments.system_control.simulated_system_control.qutip", autospec=True)
@patch("qililab.execution.buses_execution.yaml.safe_dump")
@patch("qililab.execution.buses_execution.open")
@patch("qililab.experiment.experiment.open")
@patch("qililab.experiment.experiment.os.makedirs")
class TestSimulatedExexution:
    """Unit tests checking the the execution of a simulated platform."""

    def test_execute_method_without_loop(
        self,
        mock_makedirs: MagicMock,
        mock_open: MagicMock,
        mock_open_1: MagicMock,
        mock_dump: MagicMock,
        mock_qutip: MagicMock,
        simulated_experiment: Experiment,
    ):
        """Test execute method with simulated qubit."""
        mock_qutip.mesolve.return_value.expect = [[1.0], [0.0]]
        results = simulated_experiment.execute()  # type: ignore
        mock_qutip.Options.assert_called()
        mock_qutip.ket2dm.assert_called()
        mock_qutip.mesolve.assert_called()
        mock_dump.assert_called()
        mock_open.assert_called()
        mock_open_1.assert_called()
        mock_makedirs.assert_called()
        with pytest.raises(ValueError):
            print(results.ranges)

    def test_execute_method_with_simulated_qubit(
        self,
        mock_makedirs: MagicMock,
        mock_open: MagicMock,
        mock_open_1: MagicMock,
        mock_dump: MagicMock,
        mock_qutip: MagicMock,
        simulated_experiment: Experiment,
    ):
        """Test execute method with simulated qubit."""
        mock_qutip.mesolve.return_value.expect = [[1.0], [0.0]]
        connection = MagicMock(name="API", spec=API, autospec=True)
        connection.create_liveplot.return_value = 0
        results = simulated_experiment.execute(connection=connection)  # type: ignore
        with pytest.raises(ValueError):
            results.acquisitions()
        connection.create_liveplot.assert_called_once()
        connection.send_plot_points.assert_called()
        mock_qutip.Options.assert_called()
        mock_qutip.ket2dm.assert_called()
        mock_qutip.mesolve.assert_called()
        mock_open.assert_called()
        mock_open_1.assert_called()
        mock_dump.assert_called()
        mock_makedirs.assert_called()


@patch("qililab.instruments.mini_circuits.attenuator.urllib", autospec=True)
@patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
@patch("qililab.instruments.rohde_schwarz.sgs100a.RohdeSchwarzSGS100A", autospec=True)
@patch("qililab.execution.buses_execution.yaml.safe_dump")
@patch("qililab.execution.buses_execution.open")
@patch("qililab.experiment.experiment.open")
@patch("qililab.experiment.experiment.os.makedirs")
@patch("qililab.instruments.qblox.qblox_pulsar.json.dump")
@patch("qililab.instruments.qblox.qblox_pulsar.open")
class TestExexution:
    """Unit tests checking the the execution of a platform with instruments."""

    def test_execute_method_with_nested_loop(
        self,
        mock_open_0: MagicMock,
        mock_dump_0: MagicMock,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_open_2: MagicMock,
        mock_dump_1: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        nested_experiment: Experiment,
    ):
        """Test execute method with nested loops."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar)
        nested_experiment.settings.software_average = 5
        results = nested_experiment.execute()  # type: ignore
        nested_experiment.to_dict()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        assert isinstance(results, Results)
        assert np.shape(results.acquisitions(mean=True))[2:5] == (2, 2, 2)
        assert np.shape(results.probabilities(mean=True))[2:5] == (2, 2, 2)
        mock_dump_0.assert_called()
        mock_dump_1.assert_called()
        mock_open_0.assert_called()
        mock_open_1.assert_called()
        mock_open_2.assert_called()
        mock_makedirs.assert_called()
        assert (
            results.ranges
            == np.array(
                [
                    nested_experiment.loop.range,  # type: ignore
                    nested_experiment.loop.loop.range,  # type: ignore
                    nested_experiment.loop.loop.loop.range,  # type: ignore
                ]
            )
        ).all()

    def test_execute_method_with_instruments(
        self,
        mock_open_0: MagicMock,
        mock_dump_0: MagicMock,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_open_2: MagicMock,
        mock_dump_1: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        experiment: Experiment,
    ):
        """Test run method."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar)
        results = experiment.execute()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        mock_rs.assert_called()
        mock_pulsar.assert_called()
        assert isinstance(results, Results)
        probabilities = results.probabilities()
        acquisitions = results.acquisitions()
        assert isinstance(probabilities, np.ndarray)
        assert isinstance(acquisitions, np.ndarray)
        mock_dump_0.assert_called()
        mock_dump_1.assert_called()
        mock_open_0.assert_called()
        mock_open_1.assert_called()
        mock_open_2.assert_called()
        mock_makedirs.assert_called()

    def test_execute_method_with_from_dict_experiment(
        self,
        mock_open_0: MagicMock,
        mock_dump_0: MagicMock,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_open_2: MagicMock,
        mock_dump_1: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        nested_experiment: Experiment,
    ):
        """Test run method."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar)
        experiment = Experiment.from_dict(nested_experiment.to_dict())
        results = experiment.execute()
        results_2 = nested_experiment.execute()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        assert results == results_2
        mock_rs.assert_called()
        mock_pulsar.assert_called()
        assert isinstance(results, Results)
        probabilities = results.probabilities()
        acquisitions = results.acquisitions()
        assert isinstance(probabilities, np.ndarray)
        assert isinstance(acquisitions, np.ndarray)
        mock_dump_0.assert_called()
        mock_dump_1.assert_called()
        mock_open_0.assert_called()
        mock_open_1.assert_called()
        mock_open_2.assert_called()
        mock_makedirs.assert_called()

    def test_execute_method_with_keyboard_interrupt(
        self,
        mock_open_0: MagicMock,
        mock_dump_0: MagicMock,
        mock_makedirs: MagicMock,
        mock_open_1: MagicMock,
        mock_open_2: MagicMock,
        mock_dump_1: MagicMock,
        mock_rs: MagicMock,
        mock_pulsar: MagicMock,
        mock_urllib: MagicMock,
        experiment: Experiment,
    ):
        """Test run method."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar)
        mock_pulsar.return_value.get_acquisitions.side_effect = KeyboardInterrupt()
        results = experiment.execute()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        mock_rs.assert_called()
        mock_pulsar.assert_called()
        assert isinstance(results, Results)
        mock_open_0.assert_called()
        mock_dump_0.assert_called()
        mock_open_1.assert_called()
        mock_dump_1.assert_not_called()
        mock_open_2.assert_not_called()
        mock_makedirs.assert_called()
