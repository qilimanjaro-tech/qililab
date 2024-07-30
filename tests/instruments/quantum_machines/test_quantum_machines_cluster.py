"""This file tests the the ``qm_manager`` class"""

import copy
import re
from unittest.mock import MagicMock, call, patch

import numpy as np
import pytest
from qm import Program
from qm.qua import play, program

from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.quantum_machines import QuantumMachinesCluster
from qililab.platform import Platform
from qililab.settings import Settings
from qililab.typings import Parameter
from tests.data import SauronQuantumMachines  # pylint: disable=import-error, no-name-in-module
from tests.test_utils import build_platform  # pylint: disable=import-error, no-name-in-module


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
    qmm = QuantumMachinesCluster(settings=settings)
    qmm.device = MagicMock

    return qmm


@pytest.fixture(name="qmm_with_octave")
def fixture_qmm_with_octave():
    """Fixture that returns an instance a qililab wrapper for Quantum Machines Manager."""
    settings = copy.deepcopy(SauronQuantumMachines.qmm_with_octave)
    settings.pop("name")
    qmm = QuantumMachinesCluster(settings=settings)
    qmm.device = MagicMock

    return qmm


@pytest.fixture(name="qmm_with_octave_custom_connectivity")
def fixture_qmm_with_octave_custom_connectivity():
    """Fixture that returns an instance a qililab wrapper for Quantum Machines Manager."""
    settings = copy.deepcopy(SauronQuantumMachines.qmm_with_octave_custom_connectivity)
    settings.pop("name")
    qmm = QuantumMachinesCluster(settings=settings)
    qmm.device = MagicMock

    return qmm


@pytest.fixture(name="qmm_with_opx1000")
def fixture_qmm_with_opx1000():
    """Fixture that returns an instance a qililab wrapper for Quantum Machines Manager."""
    settings = copy.deepcopy(SauronQuantumMachines.qmm_with_opx1000)
    settings.pop("name")
    qmm = QuantumMachinesCluster(settings=settings)
    qmm.device = MagicMock

    return qmm


@pytest.fixture(name="compilation_config")
def fixture_compilation_config() -> dict:
    """Fixture that returns a configuration dictionary as the QuantumMachinesCompiler would."""
    config = {
        "elements": {
            "drive_q0": {
                "operations": {"control_445e964c_fb58e912_100": "control_445e964c_fb58e912_100"},
                "RF_inputs": {"port": ("octave1", 1)},
            }
        },
        "pulses": {
            "control_445e964c_fb58e912_100": {
                "operation": "control",
                "length": 100,
                "waveforms": {"I": "445e964c", "Q": "fb58e912"},
            },
        },
        "waveforms": {"445e964c": {"type": "constant", "sample": 1.0}, "fb58e912": {"type": "constant", "sample": 0.0}},
        "octaves": {"octave1": {"RF_outputs": {1: {"gain": 0.5}}}},
    }
    return config


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


class TestQuantumMachinesCluster:
    """This class contains the unit tests for the ``QuantumMachinesCluster`` class."""

    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.Instrument.initial_setup")
    @pytest.mark.parametrize(
        "qmm_name", ["qmm", "qmm_with_octave", "qmm_with_octave_custom_connectivity", "qmm_with_opx1000"]
    )
    def test_initial_setup(
        self, mock_instrument_init: MagicMock, mock_init: MagicMock, qmm_name, request
    ):  # pylint: disable=unused-argument
        """Test QMM class initialization."""
        qmm = request.getfixturevalue(qmm_name)

        # Before initial_setup no _config should exist
        assert qmm._config_created is False and "_config" not in dir(qmm)

        qmm.initial_setup()
        mock_init.assert_called()

        assert isinstance(qmm._qmm, MagicMock)
        assert isinstance(qmm._config, dict)
        assert isinstance(qmm.config, dict)

        # Assert that the _config has been created correctly (in synch):
        assert qmm._config_created is True
        assert qmm._config == qmm.settings.to_qua_config()

    @pytest.mark.parametrize(
        "qmm_name", ["qmm", "qmm_with_octave", "qmm_with_octave_custom_connectivity", "qmm_with_opx1000"]
    )
    def test_settings(self, qmm_name, request):
        """Test QuantumMachinesClusterSettings have been set correctly"""

        qmm = request.getfixturevalue(qmm_name)
        assert isinstance(qmm.settings, Settings)

    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    @pytest.mark.parametrize(
        "qmm_name", ["qmm", "qmm_with_octave", "qmm_with_octave_custom_connectivity", "qmm_with_opx1000"]
    )
    def test_turn_on(self, mock_qmm, mock_qm, qmm_name, request):
        """Test turn_on method"""

        qmm = request.getfixturevalue(qmm_name)
        qmm.initial_setup()
        qmm.turn_on()

        assert isinstance(qmm._qm, MagicMock)
        if qmm.settings.run_octave_calibration:
            calls = [
                call(element) for element in qmm._config["elements"] if "RF_inputs" in qmm._config["elements"][element]
            ]
            qmm._qm.calibrate_element.assert_has_calls(calls)

        # Assert that the settings are still in synch:
        assert qmm._config == qmm.settings.to_qua_config()

    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    @pytest.mark.parametrize(
        "qmm_name", ["qmm", "qmm_with_octave", "qmm_with_octave_custom_connectivity", "qmm_with_opx1000"]
    )
    def test_turn_off(self, mock_qmm, mock_qm, qmm_name, request):
        """Test turn_off method"""

        qmm = request.getfixturevalue(qmm_name)
        qmm.initial_setup()
        qmm.turn_on()
        qmm.turn_off()

        # Assert that the settings are still in synch:
        assert qmm._config == qmm.settings.to_qua_config()

        assert isinstance(qmm._qm, MagicMock)
        qmm._qm.close.assert_called_once()

    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_append_configuration(self, mock_qmm, mock_qm, qmm: QuantumMachinesCluster, compilation_config: dict):
        """Test update_configuration method"""
        qmm.initial_setup()
        qmm.append_configuration(configuration=compilation_config)

        assert "control_445e964c_fb58e912_100" in qmm._config["elements"]["drive_q0"]["operations"]
        assert "control_445e964c_fb58e912_100" in qmm._config["pulses"]
        assert "445e964c" in qmm._config["waveforms"]
        assert "fb58e912" in qmm._config["waveforms"]

        # Assert that the `settings.to_qua_config()`` are a subset of the `appended_configuration``, and in synch:
        for k, v in qmm.settings.to_qua_config().items():
            if k != "elements" and v:
                assert v == qmm._config[k]
            if k == "elements":
                for element in v:
                    for key, value in v[element].items():
                        if value:
                            assert value == qmm._config[k][element][key]

    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_append_configuration_after_turn_on(
        self, mock_qmm, mock_qm, qmm: QuantumMachinesCluster, compilation_config: dict
    ):
        """Test update_configuration method"""
        qmm.initial_setup()
        qmm.turn_on()
        qmm.append_configuration(configuration=compilation_config)

        qmm._qmm.open_qm.call_count == 2
        assert isinstance(qmm._qm, MagicMock)

        # Assert that the `settings.to_qua_config()`` are a subset of the `appended_configuration``, and in synch:
        for k, v in qmm.settings.to_qua_config().items():
            if k != "elements" and v:
                assert v == qmm._config[k]
            if k == "elements":
                for element in v:
                    for key, value in v[element].items():
                        if value:
                            assert value == qmm._config[k][element][key]

    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_append_configuration_without_initial_setup_raises_error(
        self, mock_qmm, mock_qm, qmm: QuantumMachinesCluster, compilation_config: dict
    ):
        """Test update_configuration method raises an error when no config dict has been set."""
        with pytest.raises(
            ValueError,
            match=re.escape("The QM `config` dictionary does not exist. Please run `initial_setup()` first."),
        ):
            qmm.append_configuration(configuration=compilation_config)

    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_compile(self, mock_qmm, mock_qm, qmm: QuantumMachinesCluster, qua_program: Program):
        qmm.initial_setup()
        qmm.turn_on()

        assert len(qmm._compiled_program_cache) == 0
        qmm._qm.compile.return_value = "123"

        compile_program_id = qmm.compile(qua_program)
        assert len(qmm._compiled_program_cache) == 1
        assert compile_program_id == "123"

        compile_program_id = qmm.compile(qua_program)
        assert len(qmm._compiled_program_cache) == 1
        assert compile_program_id == "123"

        # Assert that the settings are still in synch:
        assert qmm._config == qmm.settings.to_qua_config()

    @patch("qm.QuantumMachine")
    def test_run(
        self, mock_qm: MagicMock, qmm: QuantumMachinesCluster, qua_program: Program
    ):  # pylint: disable=unused-argument
        """Test execute method"""
        mock_qm.return_value.execute.return_value = MagicMock
        qmm._qm = mock_qm
        job = qmm.run(qua_program)

        assert isinstance(job, MagicMock)

        # Assert that the settings are in synch:
        assert qmm._config_created is False and "_config" not in dir(qmm)

    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_run_compiled_program(self, mock_qmm, mock_qm, qmm: QuantumMachinesCluster, qua_program: Program):
        qmm.initial_setup()
        qmm.turn_on()

        qmm._qm.compile.return_value = "123"

        compile_program_id = qmm.compile(qua_program)
        _ = qmm.run_compiled_program(compile_program_id)

        # CHANGES: qm.queue.add_compiled() -> qm.add_compiled()
        qmm._qm.queue.add_compiled.assert_called_once_with(compile_program_id)
        # CHANGES: job.wait_for_execution() is deprecated and will be removed in the future. Please use job.wait_until("Running") instead.
        # The following stopped working in testing, but we have verified that works in hardware, so I remove it temporarily.
        # qmm._qm.queue.add_compiled.return_value.wait_until.assert_called_once()

        # Assert that the settings are still in synch:
        assert qmm._config == qmm.settings.to_qua_config()

    def test_get_acquisitions(self, qmm: QuantumMachinesCluster):
        """Test get_acquisitions method"""
        job = MockJob()
        results = qmm.get_acquisitions(job)

        assert isinstance(results, dict)
        assert "I" in results
        assert "Q" in results

        # Assert that the settings are in synch:
        assert qmm._config_created is False and "_config" not in dir(qmm)

    @patch("qm.QuantumMachine")
    def test_simulate(
        self, mock_qm: MagicMock, qmm: QuantumMachinesCluster, qua_program: Program
    ):  # pylint: disable=unused-argument
        """Test simulate method"""
        mock_qm.return_value.simulate.return_value = MagicMock
        qmm._qm = mock_qm
        job = qmm.simulate(qua_program)

        assert isinstance(job, MagicMock)

        # Assert that the settings are in synch:
        assert qmm._config_created is False and "_config" not in dir(qmm)

    @pytest.mark.parametrize(
        "bus, parameter, value",
        [
            ("drive_q0_rf", Parameter.LO_FREQUENCY, 6e9),
            ("drive_q0_rf", Parameter.IF, 20e6),
            ("drive_q0_rf", Parameter.GAIN, 0.001),
            ("readout_q0_rf", Parameter.LO_FREQUENCY, 6e9),
            ("readout_q0_rf", Parameter.IF, 20e6),
            ("readout_q0_rf", Parameter.GAIN, 0.001),
        ],
    )
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_set_parameter_of_bus_method_with_octave(
        self,
        mock_qmm,
        mock_qm,
        bus: str,
        parameter: Parameter,
        value: float | str | bool,
        qmm_with_octave: QuantumMachinesCluster,
    ):
        """Test the setup method with float value"""
        qmm_with_octave.initial_setup()
        qmm_with_octave.turn_on()
        qmm_with_octave._config = qmm_with_octave.settings.to_qua_config()

        qmm_with_octave.set_parameter_of_bus(bus, parameter, value)
        if parameter == Parameter.LO_FREQUENCY:
            qmm_with_octave._qm.octave.set_lo_frequency.assert_called_once()
        if parameter == Parameter.GAIN:
            qmm_with_octave._qm.octave.set_rf_output_gain.assert_called_once()
        if parameter == Parameter.IF:
            assert value == qmm_with_octave._intermediate_frequency[bus]

        # Assert that the settings are still in synch:
        assert qmm_with_octave._config == qmm_with_octave.settings.to_qua_config()

    @pytest.mark.parametrize(
        "bus, parameter, value",
        [
            ("drive_q0", Parameter.IF, 20e6),
        ],
    )
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_set_parameter_of_bus_method(
        self, mock_qmm, mock_qm, bus: str, parameter: Parameter, value: float | str | bool, qmm: QuantumMachinesCluster
    ):
        """Test the setup method with float value"""
        qmm.initial_setup()
        qmm.turn_on()
        qmm._config = qmm.settings.to_qua_config()

        qmm.set_parameter_of_bus(bus, parameter, value)
        if parameter == Parameter.IF:
            assert value == qmm_with_octave._intermediate_frequency[bus]

        # Assert that the settings are still in synch:
        assert qmm._config == qmm.settings.to_qua_config()

    @pytest.mark.parametrize(
        "bus, parameter, value",
        [
            ("drive_q0", Parameter.IF, 17e6),
        ],
    )
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_set_parameter_without_connection_changes_settings(
        self, mock_qmm, mock_qm, bus: str, parameter: Parameter, value: float | str | bool, qmm: QuantumMachinesCluster
    ):
        """Test that both the local `settings` and `_config` are changed by the set method without connection."""

        # Set intermidiate frequency to 17e6 locally
        qmm.set_parameter_of_bus(bus, parameter, value)
        qmm.initial_setup()

        # Test that both the local `settings` and `_config` have been changed to 17e6:
        assert qmm._config == qmm.settings.to_qua_config()
        ## Test `_config` QUA dictionary:
        assert qmm._config["elements"][bus][parameter] == value
        ## Test `settings` qililab dictionary:
        assert qmm.settings.to_qua_config()["elements"][bus][parameter] == value

    @pytest.mark.parametrize(
        "bus, parameter, value",
        [
            ("drive_q0", Parameter.LO_FREQUENCY, 6e9),
            ("drive_q0", Parameter.GAIN, 0.001),
        ],
    )
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_set_parameter_of_bus_method_raises_error_when_parameter_is_for_octave_and_there_is_no_octave(
        self, mock_qmm, mock_qm, bus: str, parameter: Parameter, value: float | str | bool, qmm: QuantumMachinesCluster
    ):
        """Test the set_parameter_of_bus method raises exception when the parameter is for octave and there is no octave connected to the bus."""
        qmm.initial_setup()
        qmm.turn_on()
        qmm._config = qmm.settings.to_qua_config()

        with pytest.raises(
            ValueError,
            match=f"Trying to change parameter {parameter.name} in {qmm.name}, however bus {bus} is not connected to an octave.",
        ):
            qmm.set_parameter_of_bus(bus, parameter, value)

        # Assert that the settings are still in synch:
        assert qmm._config == qmm.settings.to_qua_config()

    @pytest.mark.parametrize(
        "parameter, value", [(Parameter.LO_FREQUENCY, 6e9), (Parameter.MAX_CURRENT, 0.5), (Parameter.OUT0_ATT, 0.01)]
    )
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_set_parameter_of_bus_method_raises_exception_when_bus_not_found(
        self, mock_qmm, mock_qm, parameter: Parameter, value: float | str | bool, qmm: QuantumMachinesCluster
    ):
        """Test the set_parameter_of_bus method raises exception when parameter is wrong."""
        non_existent_bus = "non_existent_bus"

        qmm.initial_setup()
        qmm.turn_on()
        with pytest.raises(ValueError, match=f"Bus {non_existent_bus} was not found in {qmm.name} settings."):
            qmm.set_parameter_of_bus(non_existent_bus, parameter, value)

        # Assert that the settings are still in synch:
        assert qmm._config == qmm.settings.to_qua_config()

    @pytest.mark.parametrize("parameter, value", [(Parameter.MAX_CURRENT, 0.001), (Parameter.OUT0_ATT, 0.0005)])
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_set_parameter_of_bus_method_raises_exception_when_parameter_not_found(
        self, mock_qmm, mock_qm, parameter: Parameter, value, qmm: QuantumMachinesCluster
    ):
        """Test the set_parameter_of_bus method raises exception when parameter is wrong."""
        qmm.initial_setup()
        qmm.turn_on()
        with pytest.raises(ParameterNotFound, match=f"Could not find parameter {parameter} in instrument {qmm.name}."):
            qmm.set_parameter_of_bus("drive_q0", parameter, value)

        # Assert that the settings are still in synch:
        assert qmm._config == qmm.settings.to_qua_config()

    @pytest.mark.parametrize(
        "bus, parameter, qmm_name",
        [
            ("drive_q0", Parameter.LO_FREQUENCY, "qmm"),
            ("drive_q0_rf", Parameter.LO_FREQUENCY, "qmm_with_octave"),
            ("drive_q0", Parameter.IF, "qmm"),
            ("readout_q0", Parameter.GAIN, "qmm"),
            ("drive_q0_rf", Parameter.GAIN, "qmm_with_octave"),
            ("readout_q0", Parameter.TIME_OF_FLIGHT, "qmm"),
            ("readout_q0", Parameter.SMEARING, "qmm"),
        ],
    )
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_get_parameter_of_bus_method(
        self,
        mock_qmm,
        mock_qm,
        bus: str,
        parameter: Parameter,
        qmm_name: QuantumMachinesCluster,
        request,
    ):
        """Test the setup method with float value"""
        qmm = request.getfixturevalue(qmm_name)
        value = qmm.get_parameter_of_bus(bus, parameter)

        settings_config_dict = qmm.settings.to_qua_config()

        config_keys = settings_config_dict["elements"][bus]

        if parameter == Parameter.LO_FREQUENCY:
            if "mixInputs" in config_keys:
                assert value == settings_config_dict["elements"][bus]["mixInputs"]["lo_frequency"]
            if "RF_inputs" in config_keys:
                port = settings_config_dict["elements"][bus]["RF_inputs"]["port"]
                assert value == settings_config_dict["octaves"][port[0]]["RF_outputs"][port[1]]["LO_frequency"]
        if parameter == Parameter.IF:
            if "intermediate_frequency" in config_keys:
                assert value == settings_config_dict["elements"][bus]["intermediate_frequency"]
        if parameter == Parameter.GAIN:
            if "mixInputs" in config_keys and "outputs" in config_keys:
                port_i = settings_config_dict["elements"][bus]["outputs"]["out1"]
                port_q = settings_config_dict["elements"][bus]["outputs"]["out2"]
                assert value == (
                    settings_config_dict["controllers"][port_i[0]]["analog_inputs"][port_i[1]]["gain_db"],
                    settings_config_dict["controllers"][port_q[0]]["analog_inputs"][port_q[1]]["gain_db"],
                )
            if "RF_inputs" in config_keys:
                port = settings_config_dict["elements"][bus]["RF_inputs"]["port"]
                assert value == settings_config_dict["octaves"][port[0]]["RF_outputs"][port[1]]["gain"]
        if parameter == Parameter.TIME_OF_FLIGHT:
            if "time_of_flight" in config_keys:
                assert value == settings_config_dict["elements"][bus]["time_of_flight"]
        if parameter == Parameter.SMEARING:
            if "smearing" in config_keys:
                assert value == settings_config_dict["elements"][bus]["smearing"]

        # Assert that the settings are in synch:
        assert qmm._config_created is False and "_config" not in dir(qmm)

    @pytest.mark.parametrize("parameter", [(Parameter.MAX_CURRENT), (Parameter.OUT0_ATT)])
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_get_parameter_of_bus_method_raises_exception_when_parameter_not_found(
        self, mock_qmm, mock_qm, parameter: Parameter, qmm: QuantumMachinesCluster
    ):
        """Test the get_parameter_of_bus method raises exception when parameter is wrong."""
        qmm.initial_setup()
        qmm.turn_on()
        with pytest.raises(ParameterNotFound):
            qmm.get_parameter_of_bus("drive_q0", parameter)

    @pytest.mark.parametrize("bus, parameter", [("drive_q0", Parameter.LO_FREQUENCY)])
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_get_parameter_after_initial_setup(
        self, mock_qmm, mock_qm, bus: str, parameter: Parameter, qmm: QuantumMachinesCluster
    ):
        """Test the get_parameter_of_bus method after and initial_setup."""

        qmm.initial_setup()
        value = qmm.get_parameter_of_bus(bus, parameter)
        config_keys = qmm._config["elements"][bus]

        if parameter == Parameter.LO_FREQUENCY:
            if "mixInputs" in config_keys:
                assert value == qmm._config["elements"][bus]["mixInputs"]["lo_frequency"]
            if "RF_inputs" in config_keys:
                port = qmm._config["elements"][bus]["RF_inputs"]["port"]
                assert value == qmm._config["octaves"][port[0]]["RF_outputs"][port[1]]["LO_frequency"]

        # Assert that the settings are still in synch:
        assert qmm._config == qmm.settings.to_qua_config()

    @pytest.mark.parametrize("bus, parameter", [("drive_q0", Parameter.LO_FREQUENCY)])
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachinesManager")
    @patch("qililab.instruments.quantum_machines.quantum_machines_cluster.QuantumMachine")
    def test_get_parameter_doesnt_create_a_config(
        self, mock_qmm, mock_qm, bus: str, parameter: Parameter, qmm: QuantumMachinesCluster
    ):
        """Test the get_parameter_of_bus method doesn't create a `_config`."""
        assert qmm._config_created is False
        qmm.get_parameter_of_bus(bus, parameter)
        assert qmm._config_created is False
