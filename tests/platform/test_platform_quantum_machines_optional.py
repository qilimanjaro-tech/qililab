import types
from types import SimpleNamespace

import pytest

from qililab.platform.platform import Platform
from qililab.qprogram.qprogram import QProgramCompilationOutput
from qililab.typings import Parameter


class _DummyBuses(dict):
    def get(self, alias):  # matches keyword usage
        return super().__getitem__(alias)


class _DummyBus:
    def __init__(self, alias, instruments, parameters=None):
        self.alias = alias
        self.instruments = instruments
        self.channels = [0]
        self._parameters = parameters or {}

    def has_adc(self) -> bool:
        return True

    def get_parameter(self, parameter: Parameter):
        return self._parameters.get(parameter)

    def upload_qpysequence(self, qpysequence):
        raise AssertionError("Qblox path should not be used in this test")

    def run(self):
        raise AssertionError("Qblox path should not be used in this test")

    def acquire_qprogram_results(self, *args, **kwargs):
        raise AssertionError("Qblox path should not be used in this test")


class _DummyQProgram:
    def __init__(self, buses):
        self.buses = buses

    def with_bus_mapping(self, *, bus_mapping):
        return self

    def with_calibration(self, *, calibration):
        return self

    def has_calibrated_waveforms_or_weights(self) -> bool:
        return False


@pytest.fixture(autouse=True)
def _restore_quantum_machines(monkeypatch):
    """Provide simple stand-ins for the Quantum Machines optional classes."""
    import qililab.platform.platform as platform_mod

    class DummyCluster:
        def __init__(self):
            self.appended = []
            self.config = None
            self.compiled = None
            self.ran = None
            self.acquisition_requests = []
            self.turn_off_called = False

        def append_configuration(self, *, configuration):
            self.appended.append(configuration)
            self.config = configuration

        def compile(self, *, program):
            self.compiled = program
            return "compiled-id"

        def run_compiled_program(self, *, compiled_program_id):
            self.ran = compiled_program_id
            return "job"

        def get_acquisitions(self, *, job):
            self.acquisition_requests.append(job)
            return {"I": [1.0], "Q": [2.0]}

        def turn_off(self):
            self.turn_off_called = True

    captured_kwargs: dict[str, object] = {}

    class DummyCompiler:
        def compile(self, **kwargs):
            captured_kwargs.clear()
            captured_kwargs.update(kwargs)
            return "compiler-output"

    def compiler_factory():
        return DummyCompiler()

    class DummyQMOutput:
        def __init__(self, qprogram, qua, configuration, measurements):
            self.qprogram = qprogram
            self.qua = qua
            self.configuration = configuration
            self.measurements = measurements

    class DummyQMResult:
        def __init__(self, bus, *streams):
            self.bus = bus
            self.streams = streams
            self.threshold = None

        def set_classification_threshold(self, threshold):
            self.threshold = threshold

    monkeypatch.setattr(platform_mod, "QuantumMachinesCluster", DummyCluster)
    monkeypatch.setattr(platform_mod, "QuantumMachinesCompiler", compiler_factory)
    monkeypatch.setattr(platform_mod, "QuantumMachinesCompilationOutput", DummyQMOutput)
    monkeypatch.setattr(platform_mod, "QuantumMachinesMeasurementResult", DummyQMResult)
    monkeypatch.setattr(platform_mod, "generate_qua_script", lambda *args, **kwargs: "qua-script")

    return types.SimpleNamespace(
        module=platform_mod,
        Cluster=DummyCluster,
        Compiler=DummyCompiler,
        Output=DummyQMOutput,
        Result=DummyQMResult,
        captured_kwargs=captured_kwargs,
    )


def test_compile_qprogram_uses_quantum_machines(monkeypatch, _restore_quantum_machines):
    platform_mod = _restore_quantum_machines.module

    cluster_instance = platform_mod.QuantumMachinesCluster()
    bus = _DummyBus(
        alias="qm_bus",
        instruments=[cluster_instance],
        parameters={
            Parameter.THRESHOLD: 0.5,
            Parameter.THRESHOLD_ROTATION: 0.25,
        },
    )

    platform = Platform.__new__(Platform)
    platform.buses = _DummyBuses({"qm_bus": bus})

    qprogram = _DummyQProgram(["qm_bus"])

    result = platform.compile_qprogram(qprogram).quantum_machines

    assert result == "compiler-output"
    assert _restore_quantum_machines.captured_kwargs["thresholds"]["qm_bus"] == pytest.approx(0.5)
    assert _restore_quantum_machines.captured_kwargs["threshold_rotations"]["qm_bus"] == pytest.approx(0.25)


def test_execute_compilation_output_quantum_machines(_restore_quantum_machines):
    platform_mod = _restore_quantum_machines.module

    cluster_instance = platform_mod.QuantumMachinesCluster()
    bus = _DummyBus(alias="qm_bus", instruments=[cluster_instance])

    platform = Platform.__new__(Platform)
    platform.buses = _DummyBuses({"qm_bus": bus})

    qprogram = _DummyQProgram(["qm_bus"])

    measurement = SimpleNamespace(bus="qm_bus", result_handles=["I", "Q"], threshold=0.7)
    output = platform_mod.QuantumMachinesCompilationOutput(
        qprogram=qprogram,
        qua="qua-program",
        configuration={"cfg": 1},
        measurements=[measurement],
    )

    results = platform.execute_compilation_output(QProgramCompilationOutput(quantum_machines=output), None)

    cluster = bus.instruments[0]
    assert cluster.compiled == "qua-program"
    assert cluster.ran == "compiled-id"
    assert cluster.acquisition_requests == ["job"]

    measurement_result = results.results["qm_bus"][0]
    assert measurement_result.streams == ([1.0], [2.0])
    assert measurement_result.threshold == pytest.approx(0.7)
    assert not cluster.turn_off_called
