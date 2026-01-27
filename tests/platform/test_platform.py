"""Tests for the Platform class."""

import copy
import io
import re
import warnings
from pathlib import Path
from queue import Queue
from types import MethodType, SimpleNamespace
from unittest.mock import ANY, MagicMock, create_autospec, patch
import logging

import numpy as np
import pytest
from qilisdk.digital import Circuit, M, X
from qililab.data_management import build_platform as platform_build_platform
from qililab.qprogram import QbloxCompilationOutput
from qililab.qprogram.qdac_compiler import QdacCompilationOutput
from qililab.qprogram.qprogram import QProgramCompilationOutput
from qpysequence import Sequence, Waveforms
from ruamel.yaml import YAML
from tests.data import (
    Galadriel,
    SauronQDevil,
    SauronQuantumMachines,
    SauronSpiRack,
    SauronYokogawa,
)

from tests.test_utils import build_platform


from qililab import Arbitrary, save_platform
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.exceptions import ExceptionGroup
from qililab.extra.quantum_machines import QuantumMachinesCluster, QuantumMachinesMeasurementResult
from qililab.instrument_controllers import InstrumentControllers
from qililab.instrument_controllers.qblox import QbloxClusterController
from qililab.instruments import SGS100A
from qililab.instruments.instruments import Instruments
from qililab.instruments.qblox import QbloxModule
from qililab.instruments.qdevil import QDevilQDac2
from qililab.platform import Bus, Buses, Platform
from qililab.core.variables import Domain
from qililab.qprogram import Calibration, Experiment, QProgram, QbloxCompilationOutput
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
from qililab.result.database import get_db_manager
from qililab.result.qprogram.qprogram_results import QProgramResults
from qililab.result.qprogram.qblox_measurement_result import QbloxMeasurementResult
from qililab.settings import AnalogCompilationSettings, DigitalCompilationSettings, Runcard
from qililab.settings.analog.flux_control_topology import FluxControlTopology
from qililab.settings.digital.gate_event import GateEvent
from qililab.typings.enums import InstrumentName, Parameter
from qilisdk.qprogram.waveforms import Chained, IQPair, Ramp, Square

@pytest.fixture(name="platform")
def fixture_platform():
    return build_platform(runcard=Galadriel.runcard)


@pytest.fixture(name="platform_qblox_qdac")
def fixture_platform_qblox_qdac():
    return platform_build_platform(runcard="tests/runcards/qblox_and_qdac.yml")


@pytest.fixture(name="platform_qm_qdac")
def fixture_platform_qm_qdac():
    return platform_build_platform(runcard="tests/runcards/qm_and_qdac.yml")


@pytest.fixture(name="platform_quantum_machines")
def fixture_platform_quantum_machines():
    return build_platform(runcard=SauronQuantumMachines.runcard)


@pytest.fixture(name="platform_spi")
def fixture_platform_spi():
    return build_platform(runcard=SauronSpiRack.runcard)


@pytest.fixture(name="platform_qdevil")
def fixture_platform_qdevil():
    return build_platform(runcard=SauronQDevil.runcard)


@pytest.fixture(name="platform_yokogawa")
def fixture_platform_yokogawa():
    return build_platform(runcard=SauronYokogawa.runcard)


@pytest.fixture(name="runcard")
def fixture_runcard():
    return Runcard(**copy.deepcopy(Galadriel.runcard))


@pytest.fixture(name="platform_with_orphan_digital_bus")
def fixture_platform_with_orphan_digital_bus():
    """
    Platform fixture where a bus alias is defined in runcard.digital.buses
    but not in the main runcard.buses list.
    The input 'runcard' is a deepcopy from Galadriel.runcard.
    """
    # Start from base Galadriel runcard
    runcard = copy.deepcopy(Galadriel.runcard)

    # Adding an orphan digital flux bus to the platform
    # Notice the need to be flux, since those are the ones that get always loaded when compiling.
    orphan_alias = "orphan_digital_q2_flux_bus_that_does_not_exist_in_main_buses"
    runcard["digital"]["buses"][orphan_alias] = {
        "line": "flux",
        "qubits": [2],
        "delay": 0,
        "distortions": [],
    }

    # Ensure the orphan_alias is NOT in the main runcard.buses list.
    # For Galadriel.runcard, a unique name like this won't exist in the main buses.
    return build_platform(runcard)

@pytest.fixture(name="platform_galadriel_no_filter")
def fixture_platform_galadriel_no_filter():
    """
    Platform fixture where a bus alias is defined in runcard.digital.buses
    but not in the main runcard.buses list.
    The input 'runcard' is a deepcopy from Galadriel.runcard.
    """
    # Start from base Galadriel runcard
    runcard = copy.deepcopy(Galadriel.runcard)
    del runcard["instruments"][0]["filters"]

    return build_platform(runcard)

@pytest.fixture(name="qblox_results")
def fixture_qblox_results():
    return [
        {
            "scope": {
                "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
            },
            "bins": {
                "integration": {"path0": [1], "path1": [1]},
                "threshold": [0],
                "avg_cnt": [1],
            },
            "qubit": 0,
            "measurement": 0,
        },
        {
            "scope": {
                "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
            },
            "bins": {
                "integration": {"path0": [1], "path1": [1]},
                "threshold": [1],
                "avg_cnt": [1],
            },
            "qubit": 0,
            "measurement": 1,
        },
        {
            "scope": {
                "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
            },
            "bins": {
                "integration": {"path0": [1], "path1": [1]},
                "threshold": [2],
                "avg_cnt": [1],
            },
            "qubit": 1,
            "measurement": 0,
        },
        {
            "scope": {
                "path0": {"data": [], "out-of-range": False, "avg_cnt": 0},
                "path1": {"data": [], "out-of-range": False, "avg_cnt": 0},
            },
            "bins": {
                "integration": {"path0": [1], "path1": [1]},
                "threshold": [3],
                "avg_cnt": [1],
            },
            "qubit": 1,
            "measurement": 1,
        },
    ]

@pytest.fixture(name="raw_measurement_data_intertwined")
def fixture_raw_measurement_data_intertwined() -> dict:
    """Dictionary of raw measurement data as returned from QRM instruments."""
    return {"bins": {"integration": {"path0": [1, 2, 3, 4], "path1": [5, 6, 7, 8]}, "threshold": [0.1, 0.2, 0.3, 0.4], "avg_cnt":[]}, "scope": {"path0":{"data": []}, "path1":{"data": []}}}


@pytest.fixture(name="raw_measurement_data_intertwined_scope")
def fixture_raw_measurement_data_intertwinescope() -> dict:
    """Dictionary of raw measurement data as returned from QRM instruments."""
    return {"bins": {"integration": {"path0": [], "path1": []}, "threshold": [], "avg_cnt":[]}, "scope": {"path0":{"data": [1, 2, 3, 4]}, "path1":{"data": [5, 6, 7, 8]}}}

@pytest.fixture(name="flux_to_bus_topology")
def get_flux_to_bus_topology():
    flux_control_topology_dict = [
        {"flux": "phix_q0", "bus": "flux_line_phix_q0"},
        {"flux": "phiz_q0", "bus": "flux_line_phiz_q0"},
        {"flux": "phix_q1", "bus": "flux_line_phix_q1"},
        {"flux": "phiz_q1", "bus": "flux_line_phiz_q1"},
        {"flux": "phix_c0_1", "bus": "flux_line_phix_c0_1"},
        {"flux": "phiz_c0_1", "bus": "flux_line_phiz_c0_1"},
    ]
    return [FluxControlTopology(**flux_control) for flux_control in flux_control_topology_dict]


@pytest.fixture(name="calibration")
def get_calibration():
    readout_duration = 2000
    readout_amplitude = 1.0
    r_wf_I = Square(amplitude=readout_amplitude, duration=readout_duration)
    r_wf_Q = Square(amplitude=0.0, duration=readout_duration)
    readout_waveform = IQPair(I=r_wf_I, Q=r_wf_Q)
    weights_shape = Square(amplitude=1, duration=readout_duration)
    weights = IQPair(I=weights_shape, Q=weights_shape)

    measurement_qp = QProgram()
    measurement_qp.measure(bus="readout_bus", waveform=readout_waveform, weights=weights)

    calibration = Calibration()
    calibration.add_block(name="measurement", block=measurement_qp.body)

    return calibration


@pytest.fixture(name="calibration_with_preparation_block")
def get_calibration_with_preparation_block():
    readout_duration = 2000
    readout_amplitude = 1.0
    r_wf_I = Square(amplitude=readout_amplitude, duration=readout_duration)
    r_wf_Q = Square(amplitude=0.0, duration=readout_duration)
    readout_waveform = IQPair(I=r_wf_I, Q=r_wf_Q)
    weights_shape = Square(amplitude=1, duration=readout_duration)
    weights = IQPair(I=weights_shape, Q=weights_shape)

    preparation_wf = Chained(
        waveforms=[Ramp(from_amplitude=0.0, to_amplitude=1.0, duration=100), Square(amplitude=1.0, duration=200)]
    )
    preparation_qp = QProgram()
    preparation_qp.play(bus="flux_line_phix_q0", waveform=preparation_wf)
    preparation_qp.play(bus="flux_line_phiz_q0", waveform=preparation_wf)

    measurement_qp = QProgram()
    measurement_qp.measure(bus="readout_bus", waveform=readout_waveform, weights=weights)

    calibration = Calibration()
    calibration.add_block(name="preparation", block=preparation_qp.body)
    calibration.add_block(name="measurement", block=measurement_qp.body)

    return calibration


@pytest.fixture(name="anneal_qprogram")
def get_anneal_qprogram(runcard, flux_to_bus_topology):
    platform = Platform(runcard=runcard)
    platform.analog_compilation_settings = flux_to_bus_topology
    anneal_waveforms = {
        next(element.bus for element in platform.analog_compilation_settings if element.flux == "phix_q0"): Arbitrary(
            np.array([0.0, 0.0, 0.0, 1.0])
        ),
        next(element.bus for element in platform.analog_compilation_settings if element.flux == "phiz_q0"): Arbitrary(
            np.array([0.0, 0.0, 0.0, 2.0])
        ),
    }
    num_averages = 2
    num_shots = 1
    readout_duration = 2000
    readout_amplitude = 1.0
    r_wf_I = Square(amplitude=readout_amplitude, duration=readout_duration)
    r_wf_Q = Square(amplitude=0.0, duration=readout_duration)
    readout_waveform = IQPair(I=r_wf_I, Q=r_wf_Q)
    weights_shape = Square(amplitude=1, duration=readout_duration)
    weights = IQPair(I=weights_shape, Q=weights_shape)

    qp_anneal = QProgram()
    shots_variable = qp_anneal.variable("num_shots", Domain.Scalar, int)
    with qp_anneal.for_loop(variable=shots_variable, start=0, stop=num_shots, step=1):
        with qp_anneal.average(num_averages):
            for bus, waveform in anneal_waveforms.items():
                qp_anneal.play(bus=bus, waveform=waveform)
            qp_anneal.sync()
            qp_anneal.measure(bus="readout_bus", waveform=readout_waveform, weights=weights)
    return qp_anneal


@pytest.fixture(name="anneal_qprogram_with_preparation")
def get_anneal_qprogram_with_preparation(runcard, flux_to_bus_topology):
    platform = Platform(runcard=runcard)
    platform.analog_compilation_settings = flux_to_bus_topology
    anneal_waveforms = {
        next(element.bus for element in platform.analog_compilation_settings if element.flux == "phix_q0"): Arbitrary(
            np.array([0.0, 0.0, 0.0, 1.0])
        ),
        next(element.bus for element in platform.analog_compilation_settings if element.flux == "phiz_q0"): Arbitrary(
            np.array([0.0, 0.0, 0.0, 2.0])
        ),
    }
    num_averages = 2
    num_shots = 1
    readout_duration = 2000
    readout_amplitude = 1.0
    r_wf_I = Square(amplitude=readout_amplitude, duration=readout_duration)
    r_wf_Q = Square(amplitude=0.0, duration=readout_duration)
    readout_waveform = IQPair(I=r_wf_I, Q=r_wf_Q)
    weights_shape = Square(amplitude=1, duration=readout_duration)
    weights = IQPair(I=weights_shape, Q=weights_shape)
    preparation_wf = Chained(
        waveforms=[Ramp(from_amplitude=0.0, to_amplitude=1.0, duration=100), Square(amplitude=1.0, duration=200)]
    )

    qp_anneal = QProgram()
    shots_variable = qp_anneal.variable("num_shots", Domain.Scalar, int)
    with qp_anneal.for_loop(variable=shots_variable, start=0, stop=num_shots, step=1):
        with qp_anneal.average(num_averages):
            qp_anneal.play(bus="flux_line_phix_q0", waveform=preparation_wf)
            qp_anneal.play(bus="flux_line_phiz_q0", waveform=preparation_wf)
            qp_anneal.sync()
            for bus, waveform in anneal_waveforms.items():
                qp_anneal.play(bus=bus, waveform=waveform)
            qp_anneal.sync()
            qp_anneal.measure(bus="readout_bus", waveform=readout_waveform, weights=weights)
    return qp_anneal


@pytest.fixture(name="qp_quantum_machine")
def fixture_qp_quantum_machine() -> QProgram:
    qp = QProgram()
    qp.play(bus="drive_q0", waveform=Square(amplitude=1, duration=10))
    qp.wait("drive_q0", 10)
    return qp

class TestPlatformInitialization:
    """Unit tests for the Platform class initialization"""

    def test_init_method(self, runcard):
        """Test initialization of the class"""
        platform = Platform(runcard=runcard)

        assert platform.name == runcard.name
        assert isinstance(platform.name, str)
        assert isinstance(platform.digital_compilation_settings, DigitalCompilationSettings)
        assert isinstance(platform.analog_compilation_settings, AnalogCompilationSettings)
        assert isinstance(platform.instruments, Instruments)
        assert isinstance(platform.instrument_controllers, InstrumentControllers)
        assert isinstance(platform.buses, Buses)
        assert isinstance(platform.qblox_active_filter_exponential, list)
        assert isinstance(platform.qblox_active_filter_fir, bool)
        assert isinstance(platform.qblox_alias_module, list)
        assert platform._connected_to_instruments is False


class TestPlatform:
    """Unit tests checking the Platform class."""

    def test_platform_name(self, platform: Platform):
        """Test platform name."""
        assert platform.name == DEFAULT_PLATFORM_NAME

    def test_compile_circuit_invokes_transpiler_and_compiler(
        self, monkeypatch: pytest.MonkeyPatch, platform: Platform
    ):
        """Platform.compile_circuit wires transpilation and compilation stages together."""
        circuit = Circuit(2)
        circuit.add(X(0))

        transpiled_circuit = object()
        compiled_qprogram = QProgram()

        transpiler_instance = MagicMock()
        transpiler_instance.run.return_value = transpiled_circuit
        transpiler_instance.context = SimpleNamespace(
            initial_layout={0: 0, 1: 1},
            final_layout={0: 1, 1: 0},
        )

        compiler_instance = MagicMock()
        compiler_instance.compile.return_value = compiled_qprogram

        transpiler_cls = MagicMock(return_value=transpiler_instance)
        compiler_cls = MagicMock(return_value=compiler_instance)

        monkeypatch.setattr("qililab.platform.platform.CircuitTranspiler", transpiler_cls)
        monkeypatch.setattr("qililab.platform.platform.CircuitToQProgramCompiler", compiler_cls)

        qubit_mapping = {0: 1}
        nshots = 256

        result = platform.compile_circuit(circuit, nshots, qubit_mapping=qubit_mapping)

        transpiler_cls.assert_called_once_with(platform.digital_compilation_settings, qubit_mapping=qubit_mapping)
        transpiler_instance.run.assert_called_once_with(circuit)
        compiler_cls.assert_called_once_with(platform.digital_compilation_settings)
        compiler_instance.compile.assert_called_once_with(transpiled_circuit, nshots)

        assert result[0] is compiled_qprogram
        assert result[1] == {0: 1, 1: 0}

    def test_compile_circuit_with_default_mapping(
        self, monkeypatch: pytest.MonkeyPatch, platform: Platform
    ):
        """If no mapping is provided, the transpiler is invoked with qubit_mapping=None and may return None layout."""
        circuit = Circuit(1)

        transpiler_instance = MagicMock()
        transpiler_instance.run.return_value = circuit
        transpiler_instance.context = SimpleNamespace(final_layout=None)

        compiler_instance = MagicMock()
        compiler_instance.compile.return_value = QProgram()

        transpiler_cls = MagicMock(return_value=transpiler_instance)
        compiler_cls = MagicMock(return_value=compiler_instance)

        monkeypatch.setattr("qililab.platform.platform.CircuitTranspiler", transpiler_cls)
        monkeypatch.setattr("qililab.platform.platform.CircuitToQProgramCompiler", compiler_cls)

        qprogram, layout = platform.compile_circuit(circuit, nshots=5)

        transpiler_cls.assert_called_once_with(platform.digital_compilation_settings, qubit_mapping=None)
        transpiler_instance.run.assert_called_once_with(circuit)
        compiler_instance.compile.assert_called_once_with(circuit, 5)
        assert isinstance(qprogram, QProgram)
        assert layout is None

    def test_compile_circuit_without_digital_settings_raises(
        self, platform: Platform
    ):
        """Raises ValueError when digital compilation settings are missing."""
        platform.digital_compilation_settings = None

        circuit = Circuit(1)

        with pytest.raises(
            ValueError, match="Cannot compile Circuit without defining DigitalCompilationSettings."
        ):
            platform.compile_circuit(circuit, nshots=128)

    def test_execute_circuit_uses_compilation_and_execution_pipeline(
        self, monkeypatch: pytest.MonkeyPatch, platform: Platform
    ):
        """execute_circuit compiles, executes, and formats samples via helpers."""
        circuit = Circuit(1)
        circuit.add(M(0))

        compiled_qprogram = QProgram()
        logical_mapping = {0: 0}
        samples = {"0": 42}

        compile_mock = MagicMock(return_value=(compiled_qprogram, logical_mapping))
        execute_mock = MagicMock(return_value="results")
        samples_mock = MagicMock(return_value=samples)

        monkeypatch.setattr(platform, "compile_circuit", compile_mock)
        monkeypatch.setattr(platform, "execute_qprogram", execute_mock)
        monkeypatch.setattr("qililab.platform.platform.qprogram_results_to_samples", samples_mock)

        qubit_mapping = {0: 0}
        nshots = 32

        result = platform.execute_circuit(circuit, nshots, qubit_mapping=qubit_mapping)

        compile_mock.assert_called_once_with(circuit, nshots, qubit_mapping=qubit_mapping)
        execute_mock.assert_called_once_with(compiled_qprogram)
        samples_mock.assert_called_once_with("results", logical_mapping)

        assert result == samples

    def test_execute_circuit_handles_none_mapping(
        self, monkeypatch: pytest.MonkeyPatch, platform: Platform
    ):
        """execute_circuit forwards a None logical-to-physical mapping without modification."""
        circuit = Circuit(1)

        compile_mock = MagicMock(return_value=(QProgram(), None))
        execute_mock = MagicMock(return_value="results")
        samples_mock = MagicMock(return_value={"0": 1})

        monkeypatch.setattr(platform, "compile_circuit", compile_mock)
        monkeypatch.setattr(platform, "execute_qprogram", execute_mock)
        monkeypatch.setattr("qililab.platform.platform.qprogram_results_to_samples", samples_mock)

        result = platform.execute_circuit(circuit, nshots=20)

        compile_mock.assert_called_once_with(circuit, 20, qubit_mapping=None)
        execute_mock.assert_called_once_with(compile_mock.return_value[0])
        samples_mock.assert_called_once_with("results", None)
        assert result == {"0": 1}

    def test_initial_setup_no_instrument_connection(self, platform: Platform):
        """Test platform raises and error if no instrument connection."""
        platform._connected_to_instruments = False
        with pytest.raises(
            AttributeError, match="Can not do initial_setup without being connected to the instruments."
        ):
            platform.initial_setup()

    def test_set_flux_parameter_qblox_channel0(self, platform: Platform, monkeypatch: pytest.MonkeyPatch):
        """Test platform sets the expected parameter for each QBlox output channel."""
        alias_to_parameter = {
            "flux_line_q0_bus": Parameter.OFFSET_OUT0,
            "flux_line_q1_bus": Parameter.OFFSET_OUT1,
            "flux_line_q2_bus": Parameter.OFFSET_OUT2,
            "flux_line_q3_bus": Parameter.OFFSET_OUT3,
        }

        for alias, expected_parameter in alias_to_parameter.items():
            bus = platform.get_element(alias=alias)
            set_parameter_mock = MagicMock()
            monkeypatch.setattr(bus, "set_parameter", set_parameter_mock)

            platform.set_crosstalk(CrosstalkMatrix.from_buses(buses={alias: {alias: 0.1}}))
            platform.set_parameter(alias=alias, parameter=Parameter.FLUX, value=0.14)

            set_parameter_mock.assert_called_once_with(parameter=expected_parameter, value=ANY)

    def test_set_flux_parameter_spi(self, platform_spi: Platform, monkeypatch: pytest.MonkeyPatch):
        """Test SPI buses use current when setting flux."""
        bus = platform_spi.get_element(alias="spi_bus")
        set_parameter_mock = MagicMock()
        monkeypatch.setattr(bus, "set_parameter", set_parameter_mock)

        platform_spi.set_crosstalk(CrosstalkMatrix.from_buses(buses={"spi_bus": {"spi_bus": 0.1}}))
        platform_spi.set_parameter(alias="spi_bus", parameter=Parameter.FLUX, value=0.14)

        set_parameter_mock.assert_called_once_with(parameter=Parameter.CURRENT, value=ANY)

    def test_set_flux_parameter_qdevil(self, platform_qdevil: Platform, monkeypatch: pytest.MonkeyPatch):
        """Test QDevil buses use voltage when setting flux."""
        bus = platform_qdevil.get_element(alias="qdac_bus")
        set_parameter_mock = MagicMock()
        monkeypatch.setattr(bus, "set_parameter", set_parameter_mock)

        platform_qdevil.set_crosstalk(CrosstalkMatrix.from_buses(buses={"qdac_bus": {"qdac_bus": 0.1}}))
        platform_qdevil.set_parameter(alias="qdac_bus", parameter=Parameter.FLUX, value=0.14)

        set_parameter_mock.assert_called_once_with(parameter=Parameter.VOLTAGE, value=ANY)

    def test_set_flux_parameter_with_set_crosstalk(self, platform: Platform):
        """Test platform set FLUX parameter when crosstalk is given."""
        crosstalk_matrix = CrosstalkMatrix.from_buses(buses={"drive_line_q0_bus": {"drive_line_q0_bus": 0.1}})
        platform.set_crosstalk(crosstalk_matrix)
        platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.FLUX, value=0.14, channel_id=0)
        assert crosstalk_matrix == platform.crosstalk
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.FLUX, channel_id=0) == 0.14

    def test_set_flux_parameter_with_wrong_bus_raises_error(self, platform: Platform):
        """Test error raising when platform set FLUX alias is the wrong bus."""
        alias = "drive_line_q1_bus"
        crosstalk_matrix = CrosstalkMatrix.from_buses(buses={"drive_line_q0_bus": {"drive_line_q0_bus": 0.1}})
        error_string = f"{alias} not inside crosstalk matrix\n{crosstalk_matrix}"
        platform.set_crosstalk(crosstalk_matrix)
        with pytest.raises(ValueError, match=error_string):
            platform.set_parameter(alias=alias, parameter=Parameter.FLUX, value=0.14, channel_id=0)

    def test_set_flux_parameter_without_crosstalk_matrix_raises_error(self, platform: Platform):
        """Test error raised when the crostalk is not set"""
        error_string = "Crosstalk matrix has not been set"
        with pytest.raises(ValueError, match=error_string):
            platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.FLUX, value=0.14, channel_id=0)

    def test_set_flux_parameter_without_instruments_raises_error(self, platform_yokogawa: Platform):
        """Test error raised when the instruments do not match the flux parameter"""
        error_string = "Flux bus must have one of these instruments:\nQCM, QRM, QRM-RF, QCM-RF, D5a, S4g, quantum_machines_cluster, qdevil_qdac2"
        with pytest.raises(ReferenceError, match=error_string):
            crosstalk_matrix = CrosstalkMatrix.from_buses(
                buses={"yokogawa_gs200_current_bus": {"yokogawa_gs200_current_bus": 0.1}}
            )
            platform_yokogawa.set_crosstalk(crosstalk=crosstalk_matrix)
            platform_yokogawa.set_parameter(
                alias="yokogawa_gs200_current_bus",
                parameter=Parameter.FLUX,
                value=0.14,
                channel_id=0,
            )

    def test_set_flux_parameter_too_many_instruments_raises_error(self, platform: Platform):
        """Test error raised when there is more than one instrument affected by the flux"""
        error_string = "Flux bus must not have more than one of these instruments:\nQCM, QRM, QRM-RF, QCM-RF, D5a, S4g, quantum_machines_cluster, qdevil_qdac2"
        with pytest.raises(NotImplementedError, match=error_string):
            crosstalk_matrix = CrosstalkMatrix.from_buses(
                buses={"flux_line_too_many_instr": {"flux_line_too_many_instr": 0.1}}
            )
            platform.set_crosstalk(crosstalk=crosstalk_matrix)
            platform.set_parameter(
                alias="flux_line_too_many_instr",
                parameter=Parameter.FLUX,
                value=0.14,
                channel_id=0,
            )

    def test_set_flux_to_zero(self, platform: Platform):
        """Test set_flux_to_zero function."""
        crosstalk_matrix = CrosstalkMatrix.from_buses(buses={"drive_line_q0_bus": {"drive_line_q0_bus": 0.1}})
        platform.set_crosstalk(crosstalk_matrix)
        platform.set_flux_to_zero()
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.FLUX) == 0.0

    def test_set_flux_to_zero_without_crosstalk_raises_error(self, platform: Platform):
        """Test set_flux_to_zero function error without crosstalk."""
        error_string = "Crosstalk matrix has not been set"
        with pytest.raises(ValueError, match=error_string):
            platform.set_flux_to_zero()

    def test_set_bias_to_zero(self, platform: Platform):
        """Test set_bias_to_zero function."""
        crosstalk_matrix = CrosstalkMatrix.from_buses(buses={"drive_line_q0_bus": {"drive_line_q0_bus": 0.1}})
        platform.set_crosstalk(crosstalk_matrix)
        platform.set_bias_to_zero()
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.OFFSET_OUT0) == 0.0

    def test_set_bias_to_zero_without_crosstalk_raises_error(self, platform: Platform):
        """Test set_bias_to_zero function error without crosstalk."""
        error_string = "Crosstalk matrix has not been set"
        with pytest.raises(ValueError, match=error_string):
            platform.set_bias_to_zero()

    def test_set_parameter_no_instrument_connection_QBLOX(self, platform: Platform):
        """Test platform raises and error if no instrument connection."""
        platform._connected_to_instruments = False
        platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.IF, value=0.14e6, channel_id=0)
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.IF, channel_id=0) == 0.14e6

        platform.set_crosstalk(CrosstalkMatrix.from_buses(buses={"drive_line_q0_bus": {"drive_line_q0_bus": 0.1}}))
        platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.FLUX, value=0.14, channel_id=0)
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.FLUX, channel_id=0) == 0.14

    @pytest.mark.parametrize(
        "bus, parameter, value",
        [
            ("drive_q0_rf", Parameter.LO_FREQUENCY, 5e9),
            ("drive_q0_rf", Parameter.IF, 14e6),
            ("drive_q0_rf", Parameter.GAIN, 0.001),
            ("readout_q0_rf", Parameter.LO_FREQUENCY, 8e9),
            ("readout_q0_rf", Parameter.IF, 16e6),
            ("readout_q0_rf", Parameter.GAIN, 0.002),
            ("drive_q0", Parameter.IF, 13e6),
            ("flux_q0", Parameter.FLUX, 0.5),
        ],
    )
    @pytest.mark.qm
    def test_set_parameter_no_instrument_connection_QM(self, bus: str, parameter: Parameter, value: float | str | bool):
        """Test platform raises and error if no instrument connection."""
        # Overwrite platform to use Quantum Machines:
        platform = build_platform(runcard=SauronQuantumMachines.runcard)
        platform._connected_to_instruments = False

        platform.set_crosstalk(CrosstalkMatrix.from_buses(buses={bus: {bus: 1}}))
        platform.set_parameter(alias=bus, parameter=parameter, value=value)
        assert platform.get_parameter(alias=bus, parameter=parameter) == value

    def test_connect_logger(self, platform: Platform):
        platform._connected_to_instruments = True
        platform.instrument_controllers = MagicMock()
        with patch("qililab.platform.platform.logger", autospec=True) as mock_logger:
            platform.connect()
        mock_logger.info.assert_called_once_with("Already connected to the instruments")

    def test_disconnect_logger(self, platform: Platform):
        platform._connected_to_instruments = True
        platform.instrument_controllers = MagicMock()
        with patch("qililab.platform.platform.logger", autospec=True) as mock_logger:
            platform.disconnect()
        mock_logger.info.assert_called_once_with("Disconnected from instruments")

    def test_disconnect_fail_logger(self, platform: Platform):
        platform._connected_to_instruments = False
        platform.instrument_controllers = MagicMock()
        with patch("qililab.platform.platform.logger", autospec=True) as mock_logger:
            platform.disconnect()
        mock_logger.info.assert_called_once_with("Already disconnected from the instruments")

    def test_get_element_method_unknown_returns_none(self, platform: Platform):
        """Test get_element method with unknown element."""
        element = platform.get_element(alias="ABC")
        assert element is None

    # def test_get_element_with_gate(self, platform: Platform):
    #     """Test the get_element method with a gate alias."""
    #     p_gates = platform.digital_compilation_settings.keys()
    #     all(isinstance(event, GateEventSettings) for gate in p_gates for event in platform.get_element(alias=gate))

    def test_str_magic_method(self, platform: Platform):
        """Test __str__ magic method."""
        str(platform)

    def test_gates_settings_instance(self, platform: Platform):
        """Test settings instance."""
        assert isinstance(platform.digital_compilation_settings, DigitalCompilationSettings)

    def test_buses_instance(self, platform: Platform):
        """Test buses instance."""
        assert isinstance(platform.buses, Buses)

    def test_bus_0_signal_generator_instance(self, platform: Platform):
        """Test bus 0 signal generator instance."""
        element = platform.get_element(alias="rs_0")
        assert isinstance(element, SGS100A)

    def test_bus_1_awg_instance(self, platform: Platform):
        """Test bus 1 qubit readout instance."""
        element = platform.get_element(alias=f"{InstrumentName.QBLOX_QRM.value}_0")
        assert isinstance(element, QbloxModule)

    @pytest.mark.parametrize("alias", ["drive_line_q0_bus", "drive_line_q1_bus", "feedline_input_output_bus", "foobar"])
    def test_get_bus_by_alias(self, platform: Platform, alias):
        """Test get_bus_by_alias method"""
        bus = platform._get_bus_by_alias(alias)
        if alias == "foobar":
            assert bus is None
        else:
            assert bus in platform.buses

    def test_get_filter(self, platform: Platform):
        """Test Get filters"""
        #  Check that the parameters can be retrieved by bus and by module
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_AMPLITUDE_0, output_id=0) == 0.7
        assert platform.get_parameter(alias="QCM", parameter=Parameter.EXPONENTIAL_AMPLITUDE_0, output_id=0) == 0.7
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_TIME_CONSTANT_0, output_id=0) == 200
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_STATE_0, output_id=0) == "enabled"
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.FIR_COEFF, output_id=0)== [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4]
        
        #  Check that filters marked as delay_comp in the runcard have not been changed
        assert platform.get_parameter(alias="flux_line_q3_bus", parameter=Parameter.EXPONENTIAL_STATE_0, output_id=3) == "delay_comp"
        assert platform.get_parameter(alias="flux_line_q3_bus", parameter=Parameter.EXPONENTIAL_STATE_0) == "delay_comp"

        #  Check that the state of the filters have been updated to delaycomp as needed (even for modules without filters in the runcard)
        assert platform.get_parameter(alias="flux_line_q1_bus", parameter=Parameter.EXPONENTIAL_STATE_0, output_id=1) == "delay_comp"
        assert platform.get_parameter(alias="flux_line_q2_bus", parameter=Parameter.EXPONENTIAL_STATE_0, output_id=2) == "delay_comp"
        assert platform.get_parameter(alias="QRM_0", parameter=Parameter.EXPONENTIAL_STATE_0, output_id=0) == "delay_comp"
        assert platform.get_parameter(alias="QRM_0", parameter=Parameter.FIR_STATE, output_id=0) == "delay_comp"
        assert platform.get_parameter(alias="QRM-RF", parameter=Parameter.EXPONENTIAL_STATE_0, output_id=0) == "delay_comp"
        assert platform.get_parameter(alias="QRM-RF", parameter=Parameter.FIR_STATE, output_id=0) == "delay_comp"
        assert platform.get_parameter(alias="QCM-RF", parameter=Parameter.FIR_STATE, output_id=1) == "delay_comp"
        assert platform.get_parameter(alias="QCM-RF", parameter=Parameter.EXPONENTIAL_STATE_0, output_id=1) == "delay_comp"

    def test_set_filter(self, platform: Platform):
        """Test Set filters"""
        #  Check that the parameters can be set
        platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_STATE_3, value = True, output_id=0)
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_STATE_3, output_id=0) == "enabled"

        platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_STATE_2, value = False, output_id=0)
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_STATE_2, output_id=0) == "bypassed"

        platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.FIR_STATE, value = True, output_id=0)
        assert platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.FIR_STATE, output_id=0) == "enabled"

    def test_update_qblox_filter_state_fir(self, platform_galadriel_no_filter: Platform):
        """Test that the filter is created if needed"""
        platform_galadriel_no_filter.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.FIR_STATE, value = True, output_id=0)
        assert platform_galadriel_no_filter.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.FIR_STATE, output_id=0) == "enabled"
        

    def test_setting_filter_bypassed_give_warning(self, caplog, platform: Platform):
        #  Check that setting a filter as bypassed will actually put/leave it as delay_comp if needed
        platform.set_parameter(alias="QCM", parameter=Parameter.EXPONENTIAL_STATE_0, value="bypassed", output_id=1)
        with caplog.at_level(logging.WARNING):
            platform.get_parameter(alias="QCM", parameter=Parameter.EXPONENTIAL_STATE_0, output_id=1)
            assert ("Another exponential filter is marked as active hence it is not possible to disable this filter otherwise this would cause a delay with the other sequencers."
                in caplog.text)
        assert platform.get_parameter(alias="QCM", parameter=Parameter.EXPONENTIAL_STATE_0, output_id=1) == "delay_comp"

        platform.set_parameter(alias="QCM", parameter=Parameter.FIR_STATE, value="bypassed", output_id=0)
        with caplog.at_level(logging.WARNING):
            platform.get_parameter(alias="QCM", parameter=Parameter.FIR_STATE, output_id=0)
            assert ("Another FIR filter is marked as active hence it is not possible to disable this filter otherwise this would cause a delay with the other sequencers."
                in caplog.text)
        assert platform.get_parameter(alias="QCM", parameter=Parameter.FIR_STATE, output_id=0) == "delay_comp"

    def test_filter_parameter_with_wrong_output_id_raises_exception(self, platform: Platform):
        """Test that setting a filter parameter with an output_id>max_output of the instrument raises an Exception."""
        output_id = 10
        with pytest.raises(IndexError, match=f"Output {output_id} exceeds the maximum number of outputs of this QBlox module."):
            platform.set_parameter(alias="QCM", parameter=Parameter.EXPONENTIAL_STATE_0, value="bypassed", output_id=output_id)

        with pytest.raises(IndexError, match=f"Output {output_id} exceeds the maximum number of outputs of this QBlox module."):
            platform.set_parameter(alias="QCM", parameter=Parameter.FIR_STATE, value="bypassed", output_id=output_id)

    def test_print_platform(self, platform: Platform):
        """Test print platform."""
        assert str(platform) == str(YAML().dump(platform.to_dict(), io.BytesIO()))

    # I'm leaving this test here, because there is no test_instruments.py, but should be moved there when created
    def test_print_instruments(self, platform: Platform):
        """Test print instruments."""
        assert str(platform.instruments) == str(YAML().dump(platform.instruments._short_dict(), io.BytesIO()))

    def test_serialization(self, platform: Platform):
        """Test that a serialization of the Platform is possible"""
        runcard_dict = platform.to_dict()
        assert isinstance(runcard_dict, dict)

        new_platform = Platform(runcard=Runcard(**runcard_dict))
        assert isinstance(new_platform, Platform)
        assert str(new_platform) == str(platform)
        assert str(new_platform.name) == str(platform.name)
        assert str(new_platform.buses) == str(platform.buses)
        assert str(new_platform.instruments) == str(platform.instruments)
        assert str(new_platform.instrument_controllers) == str(platform.instrument_controllers)

        new_runcard_dict = new_platform.to_dict()
        assert isinstance(new_runcard_dict, dict)
        assert new_runcard_dict == runcard_dict

        newest_platform = Platform(runcard=Runcard(**new_runcard_dict))
        assert isinstance(newest_platform, Platform)
        assert str(newest_platform) == str(new_platform)
        assert str(newest_platform.name) == str(new_platform.name)
        assert str(newest_platform.buses) == str(new_platform.buses)
        assert str(newest_platform.instruments) == str(new_platform.instruments)
        assert str(newest_platform.instrument_controllers) == str(new_platform.instrument_controllers)


class TestMethods:
    """Unit tests for the methods of the Platform class."""

    def test_session_success(self):
        """Test the session method when everything works successfully."""
        # Create an autospec of the Platform class
        platform = create_autospec(Platform, instance=True)

        # Manually set the session method to the real one
        platform.session = Platform.session.__get__(platform, Platform)

        # Run the session successfully
        with platform.session():
            pass  # Simulate a successful experiment execution

        # Ensure methods were called in the correct order
        platform.connect.assert_called_once()
        platform.initial_setup.assert_called_once()
        platform.turn_on_instruments.assert_called_once()

        # Ensure cleanup is called in reverse order
        platform.turn_off_instruments.assert_called_once()
        platform.disconnect.assert_called_once()

    def test_session_with_exception(self):
        """Test the session method when an exception occurs during execution."""
        # Create an autospec of the Platform class
        platform = create_autospec(Platform, instance=True)

        # Manually set the session method to the real one
        platform.session = Platform.session.__get__(platform, Platform)

        # Simulate an exception during the experiment
        with pytest.raises(AttributeError, match="Test Error"):
            with platform.session():
                raise AttributeError("Test Error")

        # Ensure methods were called in the correct order before the exception
        platform.connect.assert_called_once()
        platform.initial_setup.assert_called_once()
        platform.turn_on_instruments.assert_called_once()

        # Ensure cleanup is still called in reverse order even after the exception
        platform.turn_off_instruments.assert_called_once()
        platform.disconnect.assert_called_once()

    def test_session_with_exception_in_setup(self):
        """Test the session method when an error occurs before turning on instruments."""
        # Create an autospec of the Platform class
        platform = create_autospec(Platform, instance=True)

        # Manually set the session method to the real one
        platform.session = Platform.session.__get__(platform, Platform)

        # Raise an exception after connect() and initial_setup() but before turn_on_instruments()
        platform.turn_on_instruments.side_effect = Exception("Instrument failure")

        # Simulate an error after connect() and initial_setup() but before turn_on_instruments()
        with pytest.raises(Exception, match="Instrument failure"):
            with platform.session():
                pass  # The exception will occur inside the context

        # Ensure methods were called until the point of failure
        platform.connect.assert_called_once()
        platform.initial_setup.assert_called_once()
        platform.turn_on_instruments.assert_called_once()

        # Ensure turn_off_instruments is not called, but disconnect is called
        platform.turn_off_instruments.assert_not_called()
        platform.disconnect.assert_called_once()

    def test_session_with_exception_in_cleanup(self):
        """Test the session method when an exception occurs during cleanup."""
        # Create an autospec of the Platform class
        platform = create_autospec(Platform, instance=True)

        # Manually set the session method to the real one
        platform.session = Platform.session.__get__(platform, Platform)

        # Simulate turn_off_instruments failing
        platform.turn_off_instruments.side_effect = Exception("Turn off instruments error")

        # Simulate no exception during the experiment, but failure during cleanup
        with pytest.raises(Exception, match="Turn off instruments error"):
            with platform.session():
                pass  # No exception during the experiment

        # Ensure methods were called in the correct order
        platform.connect.assert_called_once()
        platform.initial_setup.assert_called_once()
        platform.turn_on_instruments.assert_called_once()

        # Ensure the exception is raised in cleanup
        platform.turn_off_instruments.assert_called_once()
        platform.disconnect.assert_called_once()

    def test_session_with_multiple_exceptions_in_cleanup(self):
        """Test the session method when multiple exceptions occur during cleanup."""
        # Create an autospec of the Platform class
        platform = create_autospec(Platform, instance=True)

        # Manually set the session method to the real one
        platform.session = Platform.session.__get__(platform, Platform)

        # Simulate turn_off_instruments and disconnect failing
        platform.turn_off_instruments.side_effect = Exception("Turn off instruments error")
        platform.disconnect.side_effect = Exception("Disconnect error")

        with pytest.raises(ExceptionGroup) as exc_info:
            with platform.session():
                pass

        # Ensure ExceptionGroup has captured all exceptions
        assert len(exc_info.value.exceptions) == 2
        assert str(exc_info.value.exceptions[0]) == "Turn off instruments error"
        assert str(exc_info.value.exceptions[1]) == "Disconnect error"

        # Ensure methods were called in the correct order
        platform.connect.assert_called_once()
        platform.initial_setup.assert_called_once()
        platform.turn_on_instruments.assert_called_once()
        platform.turn_off_instruments.assert_called_once()
        platform.disconnect.assert_called_once()

    @pytest.mark.parametrize(
        "qprogram_fixture, calibration_fixture",
        [
            ("anneal_qprogram", "calibration"),
            ("anneal_qprogram_with_preparation", "calibration_with_preparation_block"),
        ],
    )
    def test_execute_anneal_program(
        self,
        platform: Platform,
        qprogram_fixture: str,
        flux_to_bus_topology: list[FluxControlTopology],
        calibration_fixture: str,
        request,
    ):
        anneal_qprogram = request.getfixturevalue(qprogram_fixture)
        calibration = request.getfixturevalue(calibration_fixture)

        mock_execute_qprogram = MagicMock()
        mock_execute_qprogram.return_value = QProgramResults()
        platform.execute_qprogram = mock_execute_qprogram  # type: ignore[method-assign]
        platform.analog_compilation_settings.flux_control_topology = flux_to_bus_topology
        transpiler = MagicMock()
        transpiler.return_value = (1, 2)

        results = platform.execute_annealing_program(
            annealing_program_dict=[{"qubit_0": {"sigma_x": 0.1, "sigma_z": 0.2}}],
            transpiler=transpiler,
            calibration=calibration,
            num_averages=2,
            num_shots=1,
        )
        qprogram = mock_execute_qprogram.call_args[1]["qprogram"].with_calibration(calibration)
        assert str(anneal_qprogram) == str(qprogram)
        assert isinstance(results, QProgramResults)

    def test_execute_anneal_program_no_measurement_raises_error(self, platform: Platform, calibration):
        mock_execute_qprogram = MagicMock()
        platform.execute_qprogram = mock_execute_qprogram  # type: ignore[method-assign]
        transpiler = MagicMock()
        transpiler.return_value = (1, 2)
        error_string = "The calibrated measurement is not present in the calibration file."
        with pytest.raises(ValueError, match=error_string):
            platform.execute_annealing_program(
                annealing_program_dict=[{"qubit_0": {"sigma_x": 0.1, "sigma_z": 0.2}}],
                transpiler=transpiler,
                calibration=calibration,
                num_averages=2,
                num_shots=1,
                measurement_block="whatever",
            )

    def test_execute_experiment(self, override_settings):
        """Test the execute_experiment method of the Platform class."""
        # Create an autospec of the Platform class
        platform = create_autospec(Platform, instance=True)

        # Manually set the execute_experiment method to the real one
        platform.execute_experiment = MethodType(Platform.execute_experiment, platform)

        # Mock database manager
        mock_database = MagicMock()
        platform.db_manager = mock_database
        platform.save_experiment_results_in_database = True

        # Create an autospec of the Experiment class and Calibration class
        mock_experiment = create_autospec(Experiment)

        expected_results_path = "mock/results/path/data.h5"

        # Mock the ExperimentExecutor to ensure it's used correctly
        with patch("qililab.platform.platform.ExperimentExecutor") as MockExecutor:
            mock_executor_instance = MockExecutor.return_value  # Mock instance of ExperimentExecutor
            mock_executor_instance.execute.return_value = expected_results_path

            # Call the method under test
            platform.db_manager = None
            with override_settings(
                experiment_results_save_in_database=False,
                experiment_live_plot_enabled=False,
                experiment_live_plot_on_slurm=False,
            ):
                results_path = platform.execute_experiment(experiment=mock_experiment)

            # Check that ExperimentExecutor was instantiated with the correct arguments
            MockExecutor.assert_called_once_with(
                platform=platform,
                experiment=mock_experiment,
                job_id=None,
                sample=None,
                cooldown=None,
            )

            # Ensure the execute method was called on the ExperimentExecutor instance
            mock_executor_instance.execute.assert_called_once()

            # Ensure that execute_experiment returns the correct value
            assert results_path == expected_results_path

    def test_execute_experiment_raises_reference_error(self, override_settings):
        """Test that execute() raises ReferenceError when get_db_manager() fails."""

        # Create an autospec of the Platform class
        platform = create_autospec(Platform, instance=True)

        # Manually set the execute_experiment method to the real one
        platform.execute_experiment = MethodType(Platform.execute_experiment, platform)

        platform.db_manager = None
        platform.save_experiment_results_in_database = True

        # Create an autospec of the Experiment class and Calibration class
        mock_experiment = create_autospec(Experiment)

        expected_results_path = "mock/results/path/data.h5"

        with override_settings(
            experiment_results_save_in_database=True,
            experiment_live_plot_enabled=False,
            experiment_live_plot_on_slurm=False,
        ):
            with patch.object(platform, "load_db_manager", side_effect=ReferenceError):
                with pytest.raises(
                    ReferenceError, match="Missing initialization information at the desired database '.ini' path."
                ):
                    # Mock the ExperimentExecutor to ensure it's used correctly
                    with patch("qililab.platform.platform.ExperimentExecutor") as MockExecutor:
                        mock_executor_instance = MockExecutor.return_value  # Mock instance of ExperimentExecutor
                        mock_executor_instance.execute.return_value = expected_results_path

                        platform.execute_experiment(experiment=mock_experiment)

    def test_execute_qprogram_with_qblox(self, platform: Platform):
        """Test that the execute method compiles the qprogram, calls the buses to run and return the results."""
        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        readout_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
        qprogram = QProgram()
        qprogram.play(bus="drive_line_q0_bus", waveform=drive_wf)
        qprogram.play(bus="drive_line_q1_bus", waveform=drive_wf)
        qprogram.sync()
        qprogram.play(bus="feedline_input_output_bus", waveform=readout_wf)
        qprogram.play(bus="feedline_input_output_bus_1", waveform=readout_wf)
        qprogram.qblox.acquire(bus="feedline_input_output_bus", weights=weights_wf)
        qprogram.qblox.acquire(bus="feedline_input_output_bus_1", weights=weights_wf)

        with (
            patch("builtins.open") as patched_open,
            patch.object(Bus, "upload_qpysequence") as upload,
            patch.object(Bus, "run") as run,
            patch.object(Bus, "acquire_qprogram_results") as acquire_qprogram_results,
            patch.object(QbloxModule, "sync_sequencer") as sync_sequencer,
            patch.object(QbloxModule, "desync_sequencer") as desync_sequencer,
        ):
            acquire_qprogram_results.return_value = [123]
            first_execution_results = platform.execute_qprogram(qprogram=qprogram)

            acquire_qprogram_results.return_value = [456]
            second_execution_results = platform.execute_qprogram(qprogram=qprogram)

            _ = platform.execute_qprogram(qprogram=qprogram, debug=True)

        # assert upload executed only once (4 because there are 4 buses)
        assert upload.call_count == 4

        # assert run executed all three times (12 because there are 4 buses)
        assert run.call_count == 12
        assert acquire_qprogram_results.call_count == 6  # only readout buses
        assert sync_sequencer.call_count == 12  # called as many times as run
        assert desync_sequencer.call_count == 12
        assert first_execution_results.results["feedline_input_output_bus"] == [123]
        assert first_execution_results.results["feedline_input_output_bus_1"] == [123]
        assert second_execution_results.results["feedline_input_output_bus"] == [456]
        assert second_execution_results.results["feedline_input_output_bus_1"] == [456]

        # assure only one debug was called
        assert patched_open.call_count == 1

    def test_execute_qprogram_with_qblox_and_qdac(self, platform_qblox_qdac: Platform):
        """Test that the execute method compiles the qprogram, calls the buses to run and return the results."""
        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        readout_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        qdac_wf = Square(amplitude=1.0, duration=100)
        qprogram = QProgram()
        qprogram.play(bus="qdac_bus_1", waveform=qdac_wf)
        qprogram.set_offset(bus="qdac_bus_2", offset_path0=1)
        qprogram.set_trigger(bus="qdac_bus_1", duration=10e-6, outputs=1)
        qprogram.play(bus="drive", waveform=drive_wf)
        qprogram.measure(bus="resonator", waveform=readout_wf, weights=weights_wf)

        with (
            patch("builtins.open") as patched_open,
            patch.object(Bus, "upload_qpysequence") as upload,
            patch.object(Bus, "run") as run,
            patch.object(Bus, "acquire_qprogram_results") as acquire_qprogram_results,
            patch.object(QbloxModule, "sync_sequencer") as sync_sequencer,
            patch.object(QbloxModule, "desync_sequencer") as desync_sequencer,
            # Mock Qdac functions without connecting
            patch.object(QDevilQDac2, "upload_voltage_list") as upload_voltage_list,
            patch.object(QDevilQDac2, "set_start_marker_external_trigger") as set_start_marker_external_trigger,
            patch.object(QDevilQDac2, "start") as start,
        ):
            acquire_qprogram_results.return_value = [123]
            first_execution_results = platform_qblox_qdac.execute_qprogram(qprogram=qprogram)

            acquire_qprogram_results.return_value = [456]
            second_execution_results = platform_qblox_qdac.execute_qprogram(qprogram=qprogram)

            _ = platform_qblox_qdac.execute_qprogram(qprogram=qprogram, debug=True)

        # assert upload executed only once (2 because there are 2 buses)
        assert upload.call_count == 2

        # assert run executed all three times (6 because there are 2 buses)
        assert run.call_count == 6
        assert acquire_qprogram_results.call_count == 3  # only readout buses
        assert sync_sequencer.call_count == 6  # called as many times as run
        assert desync_sequencer.call_count == 6
        assert first_execution_results.results["resonator"] == [123]
        assert second_execution_results.results["resonator"] == [456]
        assert upload_voltage_list.call_count == 3  # called as many times as executes
        assert set_start_marker_external_trigger.call_count == 3  # called as many times as executes
        assert start.call_count == 3  # called as many times as executes

        # assure only one debug was called
        assert patched_open.call_count == 1

    def test_execute_qprogram_with_qblox_and_qdac_back(self, platform_qblox_qdac: Platform):
        """Test that the execute method compiles the qprogram, calls the buses to run and return the results."""
        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        readout_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        qdac_wf = Square(amplitude=1.0, duration=100)
        qprogram = QProgram()
        qprogram.play(bus="qdac_bus_1", waveform=qdac_wf)
        qprogram.set_offset(bus="qdac_bus_2", offset_path0=1)
        qprogram.wait_trigger(bus="qdac_bus_1", duration=10e-6, port=1)
        qprogram.play(bus="drive", waveform=drive_wf)
        qprogram.measure(bus="resonator", waveform=readout_wf, weights=weights_wf)

        with (
            patch("builtins.open") as patched_open,
            patch.object(Bus, "upload_qpysequence") as upload,
            patch.object(Bus, "run") as run,
            patch.object(Bus, "acquire_qprogram_results") as acquire_qprogram_results,
            patch.object(QbloxModule, "sync_sequencer") as sync_sequencer,
            patch.object(QbloxModule, "desync_sequencer") as desync_sequencer,
            # Mock Qdac functions without connecting
            patch.object(QDevilQDac2, "upload_voltage_list") as upload_voltage_list,
            patch.object(QDevilQDac2, "set_in_external_trigger") as set_in_external_trigger,
            patch.object(QDevilQDac2, "start") as start,
        ):
            acquire_qprogram_results.return_value = [123]
            first_execution_results = platform_qblox_qdac.execute_qprogram(qprogram=qprogram)

            acquire_qprogram_results.return_value = [456]
            second_execution_results = platform_qblox_qdac.execute_qprogram(qprogram=qprogram)

            _ = platform_qblox_qdac.execute_qprogram(qprogram=qprogram, debug=True)

        # assert upload executed only once (2 because there are 2 buses)
        assert upload.call_count == 2

        # assert run executed all three times (6 because there are 2 buses)
        assert run.call_count == 6
        assert acquire_qprogram_results.call_count == 3  # only readout buses
        assert sync_sequencer.call_count == 6  # called as many times as run
        assert desync_sequencer.call_count == 6
        assert first_execution_results.results["resonator"] == [123]
        assert second_execution_results.results["resonator"] == [456]
        assert upload_voltage_list.call_count == 3  # called as many times as executes
        assert set_in_external_trigger.call_count == 3  # called as many times as executes
        assert start.call_count == 3  # called as many times as executes

        # assure only one debug was called
        assert patched_open.call_count == 1

    def test_execute_qprogram_with_qblox_and_qdac_timeout_error(self, platform_qblox_qdac: Platform):
        """Test that the execute_qprogram method raises the exception if the qprogram failes"""

        # Setup mock QbloxCompilationOutput and QdacCompilationOutput
        mock_output = MagicMock(spec=QbloxCompilationOutput)
        mock_qdac_output = MagicMock(spec=QdacCompilationOutput)
        mock_output.sequences = {"bus1": MagicMock()}
        mock_output.acquisitions = {"bus1": MagicMock()}

        mock_qdac_output.trigger_position = "front"
        mock_qdac = MagicMock()
        mock_qdac_output.qdac = mock_qdac

        mock_bus = MagicMock()
        mock_bus.has_adc.return_value = False
        mock_bus.instruments = [MagicMock(spec=QbloxModule)]
        mock_bus.channels = [0]

        # Raise TimeoutError on run
        mock_bus.run.side_effect = TimeoutError("Simulated timeout")

        platform_qblox_qdac.buses.get = MagicMock(return_value=mock_bus)
        platform_qblox_qdac._qpy_sequence_cache = {}
        platform_qblox_qdac.trigger_runs = 0

        mock_output.qprogram = MagicMock(spec=QProgram)
        mock_output.qprogram.qblox = MagicMock(spec=QProgram._QbloxInterface)
        mock_output.qprogram.qblox.trigger_network_required = []

        with pytest.raises(TimeoutError):
            platform_qblox_qdac._execute_qblox_compilation_output(
                output=QProgramCompilationOutput(qblox=mock_output, qdac=mock_qdac_output), debug=False
            )

        # Assert it retried 3 times (initial + 3 retries = 4 attempts)
        assert mock_bus.run.call_count == 4

    @pytest.mark.qm
    def test_execute_qprogram_with_quantum_machines_and_qdac(self, platform_qm_qdac: Platform):
        """Test that the execute method compiles the qprogram, calls the buses to run and return the results."""
        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        readout_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        qdac_wf = Square(amplitude=1.0, duration=100)
        qprogram = QProgram()
        qprogram.play(bus="qdac_bus_1", waveform=qdac_wf)
        qprogram.set_offset(bus="qdac_bus_2", offset_path0=1)
        qprogram.set_trigger(bus="qdac_bus_1", duration=10e-6, outputs=1)
        qprogram.play(bus="drive", waveform=drive_wf)
        qprogram.measure(bus="readout", waveform=readout_wf, weights=weights_wf)

        with (
            patch("builtins.open") as patched_open,
            patch("qililab.platform.platform.generate_qua_script", return_value=None) as generate_qua,
            patch.object(QuantumMachinesCluster, "config") as config,
            patch.object(QuantumMachinesCluster, "append_configuration") as append_configuration,
            patch.object(QuantumMachinesCluster, "compile") as compile_program,
            patch.object(QuantumMachinesCluster, "run_compiled_program") as run_compiled_program,
            patch.object(QuantumMachinesCluster, "get_acquisitions") as get_acquisitions,
            # Mock Qdac functions without connecting
            patch.object(QDevilQDac2, "upload_voltage_list") as upload_voltage_list,
            patch.object(QDevilQDac2, "set_start_marker_external_trigger") as set_start_marker_external_trigger,
            patch.object(QDevilQDac2, "start") as start,
        ):
            cluster = platform_qm_qdac.get_element("qmm")
            config.return_value = cluster.settings.to_qua_config()

            get_acquisitions.return_value = {"I_0": np.array([1, 2, 3]), "Q_0": np.array([4, 5, 6])}
            first_execution_results = platform_qm_qdac.execute_qprogram(qprogram=qprogram)

            get_acquisitions.return_value = {"I_0": np.array([3, 2, 1]), "Q_0": np.array([6, 5, 4])}
            second_execution_results = platform_qm_qdac.execute_qprogram(qprogram=qprogram)

            _ = platform_qm_qdac.execute_qprogram(qprogram=qprogram, debug=True)

        # assert upload executed only once (2 because there are 2 buses)
        assert append_configuration.call_count == 3
        assert run_compiled_program.call_count == 3
        assert get_acquisitions.call_count == 3

        # assert run executed all three times (6 because there are 2 buses)
        assert "readout" in first_execution_results.results
        assert len(first_execution_results.results["readout"]) == 1
        assert isinstance(first_execution_results.results["readout"][0], QuantumMachinesMeasurementResult)
        np.testing.assert_array_equal(first_execution_results.results["readout"][0].I, np.array([1, 2, 3]))
        np.testing.assert_array_equal(first_execution_results.results["readout"][0].Q, np.array([4, 5, 6]))
        np.testing.assert_array_equal(second_execution_results.results["readout"][0].I, np.array([3, 2, 1]))
        np.testing.assert_array_equal(second_execution_results.results["readout"][0].Q, np.array([6, 5, 4]))
        assert upload_voltage_list.call_count == 3  # called as many times as executes
        assert set_start_marker_external_trigger.call_count == 3  # called as many times as executes
        assert start.call_count == 3  # called as many times as executes

        # assure only one debug was called
        assert patched_open.call_count == 1
        assert generate_qua.call_count == 1

    def test_execute_qprogram_with_qblox_distortions(self, platform: Platform):
        drive_wf = Square(amplitude=1.0, duration=4)
        qprogram = QProgram()
        qprogram.play(bus="drive_line_q0_bus", waveform=drive_wf)

        test_waveforms_q0 = Waveforms()
        test_waveforms_q0.add(array=[0.5, 1.0, 0.5, 0.0], index=0)
        test_waveforms_q0.add(array=[0.0, 0.0, 0.0, 0.0], index=1)

        with (
            patch("builtins.open"),
            patch.object(Bus, "upload_qpysequence") as upload,
            patch.object(Bus, "run"),
            patch.object(Bus, "acquire_qprogram_results"),
            patch.object(QbloxModule, "sync_sequencer"),
            patch.object(QbloxModule, "desync_sequencer"),
        ):
            _ = platform.execute_qprogram(qprogram=qprogram)
            assert test_waveforms_q0.to_dict() == upload.call_args_list[0].kwargs["qpysequence"]._waveforms.to_dict()

    @pytest.mark.qm
    def test_execute_qprogram_with_quantum_machines(self, platform_quantum_machines: Platform):
        """Test that the execute_qprogram method executes the qprogram for Quantum Machines correctly"""
        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        readout_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
        qprogram = QProgram()
        qprogram.play(bus="drive_q0_rf", waveform=drive_wf)
        qprogram.sync()
        qprogram.play(bus="readout_q0_rf", waveform=readout_wf)
        qprogram.measure(bus="readout_q0_rf", waveform=readout_wf, weights=weights_wf)

        with (
            patch("builtins.open") as patched_open,
            patch("qililab.platform.platform.generate_qua_script", return_value=None) as generate_qua,
            patch.object(QuantumMachinesCluster, "config") as config,
            patch.object(QuantumMachinesCluster, "append_configuration") as append_configuration,
            patch.object(QuantumMachinesCluster, "compile") as compile_program,
            patch.object(QuantumMachinesCluster, "run_compiled_program") as run_compiled_program,
            patch.object(QuantumMachinesCluster, "get_acquisitions") as get_acquisitions,
        ):
            cluster = platform_quantum_machines.get_element("qmm")
            config.return_value = cluster.settings.to_qua_config()

            get_acquisitions.return_value = {"I_0": np.array([1, 2, 3]), "Q_0": np.array([4, 5, 6])}
            first_execution_results = platform_quantum_machines.execute_qprogram(qprogram=qprogram)

            get_acquisitions.return_value = {"I_0": np.array([3, 2, 1]), "Q_0": np.array([6, 5, 4])}
            second_execution_results = platform_quantum_machines.execute_qprogram(qprogram=qprogram)

            _ = platform_quantum_machines.execute_qprogram(qprogram=qprogram, debug=True)

        assert compile_program.call_count == 3
        assert append_configuration.call_count == 3
        assert run_compiled_program.call_count == 3
        assert get_acquisitions.call_count == 3

        assert "readout_q0_rf" in first_execution_results.results
        assert len(first_execution_results.results["readout_q0_rf"]) == 1
        assert isinstance(first_execution_results.results["readout_q0_rf"][0], QuantumMachinesMeasurementResult)
        np.testing.assert_array_equal(first_execution_results.results["readout_q0_rf"][0].I, np.array([1, 2, 3]))
        np.testing.assert_array_equal(first_execution_results.results["readout_q0_rf"][0].Q, np.array([4, 5, 6]))

        assert "readout_q0_rf" in second_execution_results.results
        assert len(second_execution_results.results["readout_q0_rf"]) == 1
        assert isinstance(second_execution_results.results["readout_q0_rf"][0], QuantumMachinesMeasurementResult)
        np.testing.assert_array_equal(second_execution_results.results["readout_q0_rf"][0].I, np.array([3, 2, 1]))
        np.testing.assert_array_equal(second_execution_results.results["readout_q0_rf"][0].Q, np.array([6, 5, 4]))

        # assure only one debug was called
        assert patched_open.call_count == 1
        assert generate_qua.call_count == 1

    @pytest.mark.qm
    def test_execute_qprogram_with_quantum_machines_raises_error(self, platform_quantum_machines: Platform):
        """Test that the execute_qprogram method raises the exception if the qprogram failes"""

        error_string = "The QM `config` dictionary does not exist. Please run `initial_setup()` first."
        escaped_error_str = re.escape(error_string)
        platform_quantum_machines.compile_circuit = MagicMock()  # type: ignore # don't care about compilation
        platform_quantum_machines.compile_circuit.return_value = Exception(escaped_error_str)

        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        readout_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
        qprogram = QProgram()
        qprogram.play(bus="drive_q0_rf", waveform=drive_wf)
        qprogram.sync()
        qprogram.play(bus="readout_q0_rf", waveform=readout_wf)
        qprogram.measure(bus="readout_q0_rf", waveform=readout_wf, weights=weights_wf)

        with patch.object(QuantumMachinesCluster, "turn_off") as turn_off:
            with pytest.raises(ValueError, match=escaped_error_str):
                _ = platform_quantum_machines.execute_qprogram(qprogram=qprogram, debug=True)

        turn_off.assert_called_once_with()

    @pytest.mark.parametrize("parameter", [Parameter.AMPLITUDE, Parameter.DURATION, Parameter.PHASE])
    @pytest.mark.parametrize("gate", ["I(0)", "X(0)", "Y(0)"])
    @pytest.mark.parametrize("value", [1.0, 100, 0.0])
    def test_set_parameter_of_gates(self, parameter, gate, value, platform: Platform):
        """Test the ``get_parameter`` method with """
        platform.set_parameter(parameter=parameter, alias=gate, value=value)
        gate_settings = platform.digital_compilation_settings.gates[gate][0]
        assert gate_settings.get_parameter(parameter) == value

        platform.digital_compilation_settings = None
        with pytest.raises(ValueError):
            platform.set_parameter(parameter=parameter, alias=gate, value=value)

    @pytest.mark.parametrize("parameter", [Parameter.AMPLITUDE, Parameter.DURATION, Parameter.PHASE])
    @pytest.mark.parametrize("gate", ["I(0)", "X(0)", "Y(0)"])
    def test_get_parameter_of_gates(self, parameter, gate, platform: Platform):
        """Test the ``get_parameter`` method with """
        gate_settings = platform.digital_compilation_settings.gates[gate][0]
        assert platform.get_parameter(parameter=parameter, alias=gate) == gate_settings.get_parameter(parameter)

        platform.digital_compilation_settings = None
        with pytest.raises(ValueError):
            platform.get_parameter(parameter=parameter, alias=gate)

    @pytest.mark.parametrize("parameter", [Parameter.DRAG_COEFFICIENT, Parameter.NUM_SIGMAS])
    @pytest.mark.parametrize("gate", ["X(0)", "Y(0)"])
    def test_get_parameter_of_pulse_shapes(self, parameter, gate, platform: Platform):
        """Test the ``get_parameter`` method with """
        gate_settings = platform.digital_compilation_settings.gates[gate][0]
        assert platform.get_parameter(parameter=parameter, alias=gate) == gate_settings.get_parameter(parameter)

    def test_get_parameter_of_gates_raises_error(self, platform: Platform):
        """Test that the ``get_parameter`` method with gates raises an error when a gate is not found."""
        with pytest.raises(KeyError, match="Gate Rmw for qubits 3 not found in settings"):
            platform.get_parameter(parameter=Parameter.AMPLITUDE, alias="Rmw(3)")

    @pytest.mark.parametrize("parameter", [Parameter.FLUX])
    def test_get_flux_parameter(self, parameter, platform: Platform):
        """Test the ``get_parameter`` method with platform flux parameters. The default as 0 is created"""
        value = platform.get_parameter(parameter=parameter, alias="flux_line_phix_q0")
        assert value == 0

    def test_get_parameter_with_delay(self, platform: Platform):
        """Test the ``get_parameter`` method with the delay of a bus."""
        value = platform.get_parameter(parameter=Parameter.DELAY, alias="drive_line_q0_bus")
        assert value == 0

    @pytest.mark.parametrize(
        "parameter",
        [Parameter.IF, Parameter.GAIN, Parameter.LO_FREQUENCY, Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT2],
    )
    def test_get_parameter_of_bus(self, parameter, platform: Platform):
        """Test the ``get_parameter`` method with the parameters of a bus."""
        CHANNEL_ID = 0
        bus = platform._get_bus_by_alias(alias="drive_line_q0_bus")
        assert bus is not None
        assert bus.get_parameter(parameter=parameter, channel_id=CHANNEL_ID) == platform.get_parameter(
            parameter=parameter, alias="drive_line_q0_bus", channel_id=CHANNEL_ID
        )

    def test_no_bus_to_flux_raises_error(self, platform: Platform):
        """Test that if flux to bus topology is not specified an error is raised"""
        platform.analog_compilation_settings = None
        error_string = "Flux to bus topology not given in the runcard"
        with pytest.raises(ValueError, match=error_string):
            platform.execute_annealing_program(
                annealing_program_dict=[{}],
                calibration=MagicMock(),
                transpiler=MagicMock(),
                num_averages=2,
                num_shots=1,
            )

    def test_get_element_flux(self, platform: Platform):
        """Get the bus from a flux using get_element"""
        for flux in ["phiz_q0", "phix_c0_1"]:
            bus = platform.get_element(flux)
            assert bus.alias == next(
                flux_bus.bus
                for flux_bus in platform.analog_compilation_settings.flux_control_topology
                if flux_bus.flux == flux
            )

    def test_get_element_gate(self, platform: Platform):
        gate_events = platform.get_element("Rmw(0)_amplitude")
        assert all(isinstance(gate_event, GateEvent) for gate_event in gate_events)

    def test_parallelisation_same_bus_raises_error_qblox(self, platform: Platform):
        """Test that if parallelisation is attempted on qprograms using at least one bus in common, an error will be raised"""
        error_string = "QPrograms cannot be executed in parallel."
        qp1 = QProgram()
        qp2 = QProgram()
        qp3 = QProgram()
        qp1.play(bus="drive_line_q0_bus", waveform=Square(amplitude=1, duration=5))
        qp2.play(bus="drive_line_q1_bus", waveform=Square(amplitude=1, duration=25))
        qp2.play(bus="drive_line_q0_bus", waveform=Square(amplitude=0.5, duration=35))
        qp3.play(bus="feedline_input_output_bus_1", waveform=Square(amplitude=0.5, duration=15))

        with (
            patch("builtins.open") as patched_open,
            patch.object(Bus, "upload_qpysequence") as upload,
            patch.object(Bus, "run") as run,
            patch.object(Bus, "acquire_qprogram_results") as acquire_qprogram_results,
            patch.object(QbloxModule, "sync_sequencer") as sync_sequencer,
            patch.object(QbloxModule, "desync_sequencer") as desync_sequencer,
        ):
            qp_list = [qp1, qp2, qp3]
            with pytest.raises(ValueError, match=error_string):
                platform.execute_qprograms_parallel(qp_list, debug=True)

    @pytest.mark.qm
    def test_parallelisation_execute_quantum_machine_not_supported(self, platform_quantum_machines: Platform):
        error_string = "Parallel execution is not supported in Quantum Machines."
        qp1 = QProgram()
        qp2 = QProgram()
        qp3 = QProgram()
        qp1.play(bus="drive_q0", waveform=Square(amplitude=1, duration=5))
        qp2.play(bus="flux_q0", waveform=Square(amplitude=1, duration=25))

        with (
            patch("builtins.open") as patched_open,
            patch.object(Bus, "upload_qpysequence") as upload,
            patch.object(Bus, "run") as run,
            patch.object(Bus, "acquire_qprogram_results") as acquire_qprogram_results,
            patch.object(QbloxModule, "sync_sequencer") as sync_sequencer,
            patch.object(QbloxModule, "desync_sequencer") as desync_sequencer,
        ):
            qp_list = [qp1, qp2, qp3]
            with pytest.raises(ValueError, match=error_string):
                platform_quantum_machines.execute_qprograms_parallel(qp_list)

    def test_normalize_bus_mappings(self, platform: Platform):
        """Test the normalization of bus mappings"""
        n = 3
        bus_mappings = None

        none_mapping = platform._normalize_bus_mappings(bus_mappings=bus_mappings, n=n)
        assert isinstance(none_mapping, list)
        assert len(none_mapping) == n
        assert none_mapping == [None] * n

        bus_mappings = {"readout": "readout_q0_bus"}
        one_mapping = platform._normalize_bus_mappings(bus_mappings=bus_mappings, n=n)
        assert isinstance(one_mapping, list)
        assert len(one_mapping) == n
        for mapping in one_mapping:
            assert mapping == bus_mappings

        bus_mappings = [{"readout": "readout_q0_bus"}, None, {"readout": "readout_q2_bus"}]
        mappings = platform._normalize_bus_mappings(bus_mappings=bus_mappings, n=n)
        assert isinstance(mappings, list)
        assert len(mappings) == n
        assert mappings == bus_mappings

        bus_mappings = [{"readout": "readout_q0_bus"}, {"readout": "readout_q2_bus"}]
        with pytest.raises(ValueError, match=re.escape(f"len(bus_mappings)={len(bus_mappings)} != len(qprograms)={n}")):
            platform._normalize_bus_mappings(bus_mappings=bus_mappings, n=n)

    def test_normalize_calibrations(
        self, platform: Platform, calibration: Calibration, calibration_with_preparation_block: Calibration
    ):
        """Test the normalization of calibrations"""
        n = 3
        calibrations = None

        none_calibration = platform._normalize_calibrations(calibrations=calibrations, n=n)
        assert isinstance(none_calibration, list)
        assert len(none_calibration) == n
        assert none_calibration == [None] * n

        one_calibration = platform._normalize_calibrations(calibrations=calibration, n=n)
        assert isinstance(one_calibration, list)
        assert len(one_calibration) == n
        for calibration_instance in one_calibration:
            assert calibration_instance == calibration

        calibrations = [calibration, None, calibration_with_preparation_block]
        calibrations_normalized = platform._normalize_calibrations(calibrations=calibrations, n=n)
        assert isinstance(calibrations_normalized, list)
        assert len(calibrations_normalized) == n
        assert calibrations_normalized == calibrations

        calibrations = [calibration, calibration_with_preparation_block]
        with pytest.raises(ValueError, match=re.escape(f"len(calibrations)={len(calibrations)} != len(qprograms)={n}")):
            platform._normalize_calibrations(calibrations=calibrations, n=n)

    def test_mapped_buses(self, platform: Platform):
        """Test the mappings of buses"""
        qp_buses = set({"readout", "drive"})
        mapping = None

        mapped_buses = platform._mapped_buses(qp_buses=qp_buses, mapping=mapping)
        assert mapped_buses == qp_buses

        mapping = {"readout": "readout_q0_bus", "drive": "drive_q0_bus"}
        mapped_buses = platform._mapped_buses(qp_buses=qp_buses, mapping=mapping)
        assert len(mapped_buses) == len(mapping)
        assert "readout_q0_bus" in mapped_buses
        assert "drive_q0_bus" in mapped_buses

    def test_parallelisation_execute_qblox(self, platform: Platform):
        """Test that the execute parallelisation returns the same result per qprogram as the regular excute method"""

        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        readout_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
        drive_wf2 = IQPair(I=Square(amplitude=1.0, duration=80), Q=Square(amplitude=0.0, duration=80))
        readout_wf2 = IQPair(I=Square(amplitude=1.0, duration=150), Q=Square(amplitude=0.0, duration=150))
        weights_wf2 = IQPair(I=Square(amplitude=1.0, duration=2200), Q=Square(amplitude=0.0, duration=2200))

        qprogram1 = QProgram()
        qprogram1.play(bus="drive_line_q0_bus", waveform=drive_wf)
        qprogram1.play(bus="drive_line_q1_bus", waveform=drive_wf)
        qprogram1.sync()
        qprogram1.play(bus="feedline_input_output_bus", waveform=readout_wf)
        qprogram1.play(bus="feedline_input_output_bus_1", waveform=readout_wf)
        qprogram1.qblox.acquire(bus="feedline_input_output_bus", weights=weights_wf)

        qprogram2 = QProgram()
        qprogram2.play(bus="flux_line_q0_bus", waveform=drive_wf2)
        qprogram2.sync()
        qprogram2.play(bus="feedline_input_output_bus_2", waveform=readout_wf2)
        qprogram2.qblox.acquire(bus="feedline_input_output_bus_2", weights=weights_wf2)

        with (
            patch("builtins.open") as patched_open,
            patch.object(Bus, "upload_qpysequence") as upload,
            patch.object(Bus, "run") as run,
            patch.object(Bus, "acquire_qprogram_results") as acquire_qprogram_results,
            patch.object(QbloxModule, "sync_sequencer") as sync_sequencer,
            patch.object(QbloxModule, "desync_sequencer") as desync_sequencer,
        ):
            acquire_qprogram_results.return_value = [123]
            qp_list = [qprogram1, qprogram2]
            result_parallel = platform.execute_qprograms_parallel(qp_list, debug=True)
            non_parallel_results1 = platform.execute_qprogram(qprogram=qprogram1, debug=True)
            non_parallel_results2 = platform.execute_qprogram(qprogram=qprogram2, debug=True)
            no_qprograms = platform.execute_qprograms_parallel(qprograms=None)

            # check that each element of the result list of the parallel execution is the same as the regular execution for each respective qprograms
            assert result_parallel[0].results == non_parallel_results1.results
            assert result_parallel[1].results == non_parallel_results2.results
            assert [] == no_qprograms

    def test_calibrate_mixers(self, platform: Platform):
        """Test calibrating the Qblox mixers."""
        channel_id = 0
        cal_type = "lo"
        alias_drive_bus = "drive_line_q1_bus"
        alias_readout_bus = "feedline_input_output_bus_1"
        drive_bus = platform.get_element(alias=alias_drive_bus)
        readout_bus = platform.get_element(alias=alias_readout_bus)
        qcm_rf = drive_bus.instruments[0]
        qrm_rf = readout_bus.instruments[0]

        qcm_rf.calibrate_mixers = MagicMock()
        qrm_rf.calibrate_mixers = MagicMock()

        platform.calibrate_mixers(alias=alias_drive_bus, cal_type=cal_type, channel_id=channel_id)
        qcm_rf.calibrate_mixers.assert_called_with(cal_type, channel_id)

        platform.calibrate_mixers(alias=alias_readout_bus, cal_type=cal_type, channel_id=channel_id)
        qrm_rf.calibrate_mixers.assert_called_with(cal_type, channel_id)

        cal_type = "lo_and_sidebands"

        platform.calibrate_mixers(alias=alias_drive_bus, cal_type=cal_type, channel_id=channel_id)
        qcm_rf.calibrate_mixers.assert_called_with(cal_type, channel_id)

        platform.calibrate_mixers(alias=alias_readout_bus, cal_type=cal_type, channel_id=channel_id)
        qrm_rf.calibrate_mixers.assert_called_with(cal_type, channel_id)

        cal_type = "lo"
        non_rf_drive_bus = "drive_line_q0_bus"
        non_rf_readout_bus = "feedline_input_output_bus"

        with pytest.raises(AttributeError, match="Mixers calibration not implemented for this instrument."):
            platform.calibrate_mixers(alias=non_rf_drive_bus, cal_type=cal_type, channel_id=channel_id)

        with pytest.raises(AttributeError, match="Mixers calibration not implemented for this instrument."):
            platform.calibrate_mixers(alias=non_rf_readout_bus, cal_type=cal_type, channel_id=channel_id)

        cal_type = "lo_and_sidebands"

        with pytest.raises(AttributeError, match="Mixers calibration not implemented for this instrument."):
            platform.calibrate_mixers(alias=non_rf_drive_bus, cal_type=cal_type, channel_id=channel_id)

        with pytest.raises(AttributeError, match="Mixers calibration not implemented for this instrument."):
            platform.calibrate_mixers(alias=non_rf_readout_bus, cal_type=cal_type, channel_id=channel_id)

    @patch("qililab.platform.platform.get_db_manager")
    @patch("qililab.result.database.database_manager._load_config")
    def test_load_db_manager(self, mock_load_config, mock_get_db_manager, platform: Platform):
        """Test load_db_manager createing a database from a given path"""
        path = "~/database_test.ini"

        mock_load_config.return_value = {
            "host": "localhost",
            "user": "user",
            "passwd": "pass",
            "port": "5432",
            "database": "testdb",
            "base_path_local": "base_path_local",
            "base_path_shared": "base_path_shared",
            "data_write_folder": "data_write_folder",
        }
        mock_get_db_manager.return_value = get_db_manager(path)

        _ = platform.load_db_manager(path)

        mock_get_db_manager.assert_called_once_with(path)

    @patch("qililab.platform.platform.get_db_manager")
    @patch("qililab.result.database.database_manager._load_config")
    def test_load_db_manager_no_path(self, mock_load_config, mock_get_db_manager, platform: Platform):
        """Test load_db_manager createing a database without a given path"""
        mock_load_config.return_value = {
            "host": "localhost",
            "user": "user",
            "passwd": "pass",
            "port": "5432",
            "database": "testdb",
            "base_path_local": "base_path_local",
            "base_path_shared": "base_path_shared",
            "data_write_folder": "data_write_folder",
        }
        mock_get_db_manager.return_value = get_db_manager()

        _ = platform.load_db_manager()

        mock_get_db_manager.assert_called_once_with()

    def test_db_real_time_saving(self, platform: Platform):
        """Test db_real_time_saving function to save database from platform"""

        shape = (2, 2)
        loops = {"test_amp_loop": np.arange(0, 2)}
        experiment_name = "test_db_real_time_saving"
        mock_database = MagicMock()
        platform.db_manager = mock_database
        description = "description"

        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        qprogram = QProgram()
        qprogram.play(bus="drive_line_q0_bus", waveform=drive_wf)

        db_real_time_saving = platform.db_real_time_saving(shape, loops, experiment_name, qprogram, description)

        assert db_real_time_saving.loops == loops
        assert db_real_time_saving.optional_identifier == description
        assert db_real_time_saving.platform == platform
        assert db_real_time_saving.qprogram == qprogram
        assert db_real_time_saving.db_manager == mock_database
        assert db_real_time_saving.experiment_name == experiment_name

    @patch("h5py.File")
    def test_db_save_results(self, mock_h5file, platform: Platform):
        """Test db_save_results functionto save from database from Platform"""

        experiment_name = "experiment_name"
        loops = {"test_amp_loop": np.arange(0, 1)}
        results = np.array([[1.0, 1.0], [1.0, 1.0]])

        mock_database = MagicMock()
        platform.db_manager = mock_database
        description = "description"

        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        qprogram = QProgram()
        qprogram.play(bus="drive_line_q0_bus", waveform=drive_wf)

        platform.db_save_results(experiment_name, results, loops, qprogram, description)

        assert mock_h5file.called

    @patch("h5py.File")
    def test_db_save_results_raises_error(self, mock_h5file, platform: Platform):
        """Test db_save_results function raises an error when no database is created"""

        experiment_name = "experiment_name"
        loops = {"test_amp_loop": np.arange(0, 1)}
        results = np.array([[1.0, 1.0], [1.0, 1.0]])

        description = "description"

        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        qprogram = QProgram()
        qprogram.play(bus="drive_line_q0_bus", waveform=drive_wf)

        error_string = "Missing db_manager, try using platform.load_db_manager()."
        with pytest.raises(ReferenceError, match=error_string):
            platform.db_save_results(experiment_name, results, loops, qprogram, description)

    @patch("h5py.File")
    def test_db_save_results_loop_dict(self, mock_h5file, platform: Platform):
        """Test db_save_results functionto save from database from Platform"""

        experiment_name = "experiment_name"
        loops = {
            "test_amp_loop": {"bus": "readout", "units": "V", "parameter": Parameter.VOLTAGE, "array": np.arange(0, 1)}
        }
        results = np.array([[1.0, 1.0], [1.0, 1.0]])

        mock_database = MagicMock()
        platform.db_manager = mock_database
        description = "description"

        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        qprogram = QProgram()
        qprogram.play(bus="drive_line_q0_bus", waveform=drive_wf)

        platform.db_save_results(experiment_name, results, loops, qprogram, description)

        assert mock_h5file.called

    @patch("h5py.File")
    def test_db_save_results_raise_error_incorrect_loops(self, mock_h5file, platform: Platform):
        """Test db_save_results functionto save from database from Platform"""

        experiment_name = "experiment_name"
        loops = {"test_amp_loop": np.arange(0, 1), "test_freq_loop": np.arange(0, 1e6, 1e6)}
        results = np.array([[1.0, 1.0], [1.0, 1.0]])

        mock_database = MagicMock()
        platform.db_manager = mock_database
        description = "description"

        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        qprogram = QProgram()
        qprogram.play(bus="drive_line_q0_bus", waveform=drive_wf)

        error_string = "Number of loops must be the same as the number of dimensions of the results except for IQ"
        with pytest.raises(ValueError, match=error_string):
            platform.db_save_results(experiment_name, results, loops, qprogram, description)

    @patch("h5py.File")
    def test_db_save_results_raise_error_incorrect_loops_size(self, mock_h5file, platform: Platform):
        """Test db_save_results functionto save from database from Platform"""

        experiment_name = "experiment_name"
        loops = {"test_amp_loop": np.arange(0, 4)}
        results = np.array([[1.0, 1.0], [1.0, 1.0]])

        mock_database = MagicMock()
        platform.db_manager = mock_database
        description = "description"

        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        qprogram = QProgram()
        qprogram.play(bus="drive_line_q0_bus", waveform=drive_wf)

        error_string = "Loops dimensions must be the same than the array introduced, test_amp_loop as 4 != 2"
        with pytest.raises(ValueError, match=error_string):
            platform.db_save_results(experiment_name, results, loops, qprogram, description)

    @pytest.mark.qm    
    def test_platform_draw_quantum_machine_raises_error(
        self, qp_quantum_machine: QProgram, platform_quantum_machines: Platform
    ):

        with pytest.raises(NotImplementedError) as exc_info:
            platform_quantum_machines.draw(qp_quantum_machine)
    
        assert str(exc_info.value) == "The drawing feature is currently only supported for QBlox."

    def test_trigger_network_setup_and_reset(self, platform):
        # Build a fake compilation output with one bus “b” → trigger 5
        qp = QProgram()
        qp.qblox.trigger_network_required = {"b": 5}
        output = QProgramCompilationOutput()
        output.qblox = QbloxCompilationOutput(qprogram=qp, sequences={"b": None}, acquisitions={"b": []})

        # Stub the bus and controller
        fake_bus = MagicMock()
        fake_bus._setup_trigger_network = MagicMock()
        platform.buses.get = MagicMock(return_value=fake_bus)

        controller = MagicMock(spec=QbloxClusterController)
        controller.device = MagicMock()
        platform.instrument_controllers.elements = [controller]

        # Call the method under testus
        platform._execute_qblox_compilation_output(output)

        # Verify the two lines ran
        fake_bus._setup_trigger_network.assert_called_once_with(trigger_address=5)
        controller.device.reset_trigger_monitor_count.assert_called_once_with(address=5)

    def test_qblox_intertwined_results(self, raw_measurement_data_intertwined: dict, platform: Platform):
        """Test that the results get unintertwined."""

        bus_result = QbloxMeasurementResult(bus="drive", raw_measurement_data=raw_measurement_data_intertwined)
        intertwined = 2

        unintertwined_results = platform._unintertwined_qblox_results(bus_result, intertwined)

        assert len(unintertwined_results)==intertwined

        assert unintertwined_results[0].raw_measurement_data == {"bins": {"integration": {"path0": [1, 3], "path1": [5, 7]}, "threshold": [0.1, 0.3], "avg_cnt":[]}, "scope": {"path0":{"data": []}, "path1":{"data": []}}}
        assert unintertwined_results[1].raw_measurement_data == {"bins": {"integration": {"path0": [2, 4], "path1": [6, 8]}, "threshold": [0.2, 0.4], "avg_cnt":[]}, "scope": {"path0":{"data": []}, "path1":{"data": []}}}


    def test_qblox_intertwined_results_scope(self, raw_measurement_data_intertwined_scope: dict, platform: Platform):
        """Test that the scope results get unintertwined."""

        bus_result = QbloxMeasurementResult(bus="drive", raw_measurement_data=raw_measurement_data_intertwined_scope)
        intertwined = 2

        unintertwined_results = platform._unintertwined_qblox_results(bus_result, intertwined)

        assert len(unintertwined_results)==intertwined

        assert unintertwined_results[0].raw_measurement_data == {"bins": {"integration": {"path0": [], "path1": []}, "threshold": [], "avg_cnt":[]}, "scope": {"path0":{"data": [1, 3]}, "path1":{"data": [5, 7]}}}
        assert unintertwined_results[1].raw_measurement_data == {"bins": {"integration": {"path0": [], "path1": []}, "threshold": [], "avg_cnt":[]}, "scope": {"path0":{"data": [2, 4]}, "path1":{"data": [6, 8]}}}

    def test_setting_getting_filter_bus_error_raised(self, platform: Platform):
        #  Check that setting/getting a filter through a bus incorrectly raises the adequate error
        output_id = 1
        bus_alias = "drive_line_q0_bus"
        with pytest.raises(Exception, match=f"OutputID {output_id} is not linked to bus with alias {bus_alias}"):
            platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_STATE_0, value="bypassed", output_id=output_id)

        with pytest.raises(Exception, match="Filter parameters are controlled using output_id and not channel_id"):
            platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_STATE_0, value="bypassed", channel_id=output_id)
            
        with pytest.raises(Exception, match=f"OutputID {output_id} is not linked to bus with alias {bus_alias}"):
            platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_STATE_0, output_id=output_id)

        with pytest.raises(Exception, match="Filter parameters are controlled using output_id and not channel_id"):
            platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_STATE_0, channel_id=output_id)

    def test_setting_getting_filter_parameter_no_output_id_given(self, platform: Platform):
        old_value = 200
        new_value = 100

        time_constant = platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_TIME_CONSTANT_0,output_id=0)
        assert time_constant == old_value

        platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_TIME_CONSTANT_0, value = new_value)
        time_constant = platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.EXPONENTIAL_TIME_CONSTANT_0)
        assert time_constant == new_value

    def test_setting_getting_non_filter_parameter_error_raised(self, platform: Platform):
        sequencer = 3
        bus_alias = "drive_line_q0_bus"
        with pytest.raises(Exception, match="Only QBlox Filter parameters are controlled using output_id and not channel_id"):
            platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.IF, value=100e6, output_id=sequencer)

        with pytest.raises(Exception, match="Only QBlox Filter parameters are controlled using output_id and not channel_id"):
            platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.IF, output_id=sequencer)

        with pytest.raises(Exception, match=f"ChannelID {sequencer} is not linked to bus with alias {bus_alias}"):
            platform.set_parameter(alias="drive_line_q0_bus", parameter=Parameter.IF, value=100e6, channel_id=sequencer)

        with pytest.raises(Exception, match=f"ChannelID {sequencer} is not linked to bus with alias {bus_alias}"):
            platform.get_parameter(alias="drive_line_q0_bus", parameter=Parameter.IF, channel_id=sequencer)
