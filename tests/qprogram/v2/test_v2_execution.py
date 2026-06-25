"""Tests for the new-QProgram execution layer (``qililab.qprogram.v2``).

Covers the parts that do not need real instruments: capability classification, the SW-outer /
HW-inner structural rule, the new-AST Qblox compiler, and the software-loop executor driving a fake
hardware backend. The actual instrument I/O (``Platform._run_hw_qblox_v2``) is faked here and is
exercised separately against the mocked-cluster platform fixtures.
"""

from types import SimpleNamespace

import numpy as np
import pytest
import qprogram_qblox  # noqa: F401  (registers the qblox vendor profile + namespace)
import qprogram_qdac  # noqa: F401
from qprogram import QProgram
from qprogram.buses import BusNaming, BusSchema
from qprogram.validation import validate
from qprogram.waveforms import IQPair, Square

from qililab.qprogram.v2.capabilities import qililab_capabilities
from qililab.qprogram.v2.executor import QProgramExecutor
from qililab.qprogram.v2.partition import (
    QProgramStructureError,
    assert_sw_outer_hw_inner,
    hw_frontier,
)
from qililab.qprogram.v2.qblox_compiler import QbloxCompilerV2
from qililab.qprogram.v2.schema import RuncardBusSchema


@pytest.fixture
def schema():
    s = BusSchema(naming=BusNaming("{element}"))
    s.add_element("drive_q0", {"drive": ("IQ", False)})
    s.add_element("readout_q0", {"readout": ("IQ", True)})
    return s


@pytest.fixture
def refs(schema):
    return {
        "drive_q0": getattr(schema, "drive_q0")[0].drive,
        "readout_q0": getattr(schema, "readout_q0")[0].readout,
    }


@pytest.fixture
def bus_specs():
    return {("drive_q0", "drive"): "qblox", ("readout_q0", "readout"): "qblox"}


@pytest.fixture
def caps(bus_specs):
    return qililab_capabilities(bus_specs=bus_specs)


@pytest.fixture
def runcard_schema(schema, bus_specs, refs):
    return RuncardBusSchema(schema, bus_specs, refs)


def _waveforms():
    drive = IQPair(Square(0.5, 100), Square(0.5, 100))
    ro = IQPair(Square(0.3, 200), Square(0.3, 200))
    weights = IQPair(Square(1.0, 200), Square(1.0, 200))
    return drive, ro, weights


_RAW_SAMPLES = 16


class FakePlatform:
    """A platform stand-in that fakes instrument I/O for the executor.

    Each faked acquisition result carries ``.array`` (I/Q), ``.threshold`` (classified state) and
    ``.raw_measurement_data`` (a scope trace) so the executor's ``state`` / ``raw`` field assembly can
    be exercised; iq-only measurements simply ignore the extra fields.
    """

    def __init__(self):
        self.buses = SimpleNamespace(
            get=lambda alias: SimpleNamespace(
                has_adc=lambda: alias.startswith("readout"),
                get_parameter=lambda parameter, **kw: 24,
            )
        )
        self.set_calls: list = []
        self.get_value: float = 0.0
        self.crosstalk_calls: list = []

    def set_parameter(self, alias, parameter, value, channel_id=None):
        self.set_calls.append((alias, getattr(parameter, "value", parameter), value, channel_id))

    def set_crosstalk(self, crosstalk):
        self.crosstalk_calls.append(crosstalk)

    def get_parameter(self, alias, parameter, channel_id=None):
        return self.get_value

    def _run_hw_qblox_v2(self, output, qdac_output=None, debug=False):
        results = {}
        for acqs in output.acquisitions.values():
            for name, acq in acqs.items():
                shape = acq.shape if acq.shape else ()
                size = int(np.prod(shape)) if shape else 1
                results[name] = SimpleNamespace(
                    array=np.arange(size * 2, dtype=float).reshape((2, *shape)),
                    threshold=np.zeros((1, *shape), dtype=float),
                    raw_measurement_data={
                        "scope": {
                            "path0": {"data": np.arange(_RAW_SAMPLES, dtype=float)},
                            "path1": {"data": np.arange(_RAW_SAMPLES, dtype=float) + 0.5},
                        }
                    },
                )
        return results


# --------------------------------------------------------------------------- capabilities + plan


def test_sw_outer_hw_inner_classification(schema, refs, caps):
    drive, ro, w = _waveforms()
    qp = QProgram(schema=schema)
    f = qp.variable("freq_sw")
    with qp.for_loop(f, 0.0, 100e6, 50e6):
        qp.set_parameter("drive_q0", "frequency", f)
        with qp.average(50):
            a = qp.variable("amp")
            with qp.for_loop(a, 0.0, 1.0, 0.1):
                qp.set_gain(refs["drive_q0"], a)
                qp.play(refs["drive_q0"], drive)
                qp.measure(refs["readout_q0"], ro, w)
    diagnostics, plan = validate(qp, caps)
    assert [d for d in diagnostics if d.severity == "error"] == []
    outer_for_loop = qp.body.elements[0]
    average = outer_for_loop.elements[1]
    assert plan[outer_for_loop] == frozenset({"sw"})  # set_parameter forces software
    assert "hw" in plan[average]  # the hardware frontier


def test_variable_in_waveform_is_software_only(schema, refs, caps):
    """A swept waveform amplitude in an OUTER loop is allowed (forced software)."""
    _, ro, w = _waveforms()
    qp = QProgram(schema=schema)
    a = qp.variable("amp_sw")
    with qp.for_loop(a, 0.0, 1.0, 0.1):
        with qp.average(50):
            qp.play(refs["drive_q0"], IQPair(Square(a, 100), Square(a, 100)))
            qp.measure(refs["readout_q0"], ro, w)
    diagnostics, plan = validate(qp, caps)
    assert [d for d in diagnostics if d.severity == "error"] == []
    assert plan[qp.body.elements[0]] == frozenset({"sw"})


# --------------------------------------------------------------------------- partition rule


def test_partition_accepts_pure_hardware(schema, refs, caps):
    drive, ro, w = _waveforms()
    qp = QProgram(schema=schema)
    with qp.average(50):
        a = qp.variable("amp")
        with qp.for_loop(a, 0.0, 1.0, 0.1):
            qp.play(refs["drive_q0"], drive)
            qp.measure(refs["readout_q0"], ro, w)
    _, plan = validate(qp, caps)
    assert_sw_outer_hw_inner(qp, plan)
    assert hw_frontier(qp, plan) == [qp.body]


def test_partition_rejects_hw_op_in_software_loop(schema, refs, caps):
    drive = _waveforms()[0]
    qp = QProgram(schema=schema)
    a = qp.variable("amp")
    with qp.for_loop(a, 0.0, 1.0, 0.1):
        qp.set_gain(refs["drive_q0"], a)
        qp.set_parameter("drive_q0", "frequency", 5e9)  # forces the loop software
        qp.play(refs["drive_q0"], drive)
    _, plan = validate(qp, caps)
    with pytest.raises(QProgramStructureError):
        assert_sw_outer_hw_inner(qp, plan)


# --------------------------------------------------------------------------- compiler


def test_qblox_compiler_v2_produces_valid_sequences(schema, refs):
    drive, ro, w = _waveforms()
    qp = QProgram(schema=schema)
    with qp.average(100):
        a = qp.variable("amp")
        with qp.for_loop(a, 0.0, 1.0, 0.1):
            qp.set_gain(refs["drive_q0"], a)
            qp.set_frequency(refs["drive_q0"], 50e6)
            qp.play(refs["drive_q0"], drive)
            qp.measure(refs["readout_q0"], ro, w)
    out = QbloxCompilerV2().compile(qp, qblox_buses=["drive_q0", "readout_q0"], single_channel=[])
    assert set(out.sequences) == {"drive_q0", "readout_q0"}
    assert list(out.acquisitions["readout_q0"]) == ["readout_q0/m0"]
    # The acquisition's hardware shape is the inner for_loop length (11 inclusive points).
    assert out.acquisitions["readout_q0"]["readout_q0/m0"].shape == (11,)
    for sequence in out.sequences.values():
        assert set(sequence.todict()) == {"waveforms", "weights", "acquisitions", "program"}


# --------------------------------------------------------------------------- executor end-to-end


def test_executor_sw_outer_hw_inner(schema, refs, caps, runcard_schema):
    drive, ro, w = _waveforms()
    qp = QProgram(schema=schema)
    f = qp.variable("freq_sw")
    with qp.for_loop(f, 0.0, 100e6, 50e6):  # 3 software points
        qp.set_parameter("drive_q0", "frequency", f)
        with qp.average(50):
            a = qp.variable("amp")
            with qp.for_loop(a, 0.0, 1.0, 0.1):  # 11 hardware points
                qp.set_gain(refs["drive_q0"], a)
                qp.play(refs["drive_q0"], drive)
                qp.measure(refs["readout_q0"], ro, w)
    _, plan = validate(qp, caps)
    assert_sw_outer_hw_inner(qp, plan)
    platform = FakePlatform()
    result = QProgramExecutor(platform, qp, plan, runcard_schema).execute()
    measurement = result.measurements[0]
    assert measurement.bus == "readout_q0"
    assert measurement.data.dims == ("freq_sw", "amp", "IQ")
    assert measurement.data.shape == (3, 11, 2)
    assert not np.isnan(measurement.data.values).any()
    # one set_parameter per software iteration
    assert len(platform.set_calls) == 3


def test_executor_pure_hardware(schema, refs, caps, runcard_schema):
    drive, ro, w = _waveforms()
    qp = QProgram(schema=schema)
    with qp.average(50):
        a = qp.variable("amp")
        with qp.for_loop(a, 0.0, 1.0, 0.2):  # 6 hardware points
            qp.play(refs["drive_q0"], drive)
            qp.measure(refs["readout_q0"], ro, w)
    _, plan = validate(qp, caps)
    result = QProgramExecutor(FakePlatform(), qp, plan, runcard_schema).execute()
    measurement = result.measurements[0]
    assert measurement.data.dims == ("amp", "IQ")
    assert measurement.data.shape == (6, 2)


# --------------------------------------------------------------------------- platform.execute() end-to-end


class _IQResult:
    """Stand-in for a QbloxMeasurementResult: ``.array`` is ``(2, *hw_shape)``."""

    def __init__(self, array):
        self.array = array


def test_platform_execute_pure_hardware_with_mocked_qblox():
    """Full ``Platform.execute`` path: real platform + real compile + mocked instrument I/O."""
    from unittest.mock import patch

    from qililab.data_management import build_platform
    from qililab.instruments.qblox import QbloxModule
    from qililab.platform.components.bus import Bus

    platform = build_platform(runcard="tests/runcards/qblox_and_qdac.yml")
    drive = platform.bus_ref("drive")
    resonator = platform.bus_ref("resonator")

    qp = QProgram(schema=platform.bus_schema())
    with qp.average(100):
        qp.play(drive, IQPair(Square(1.0, 40), Square(0.0, 40)))
        qp.measure(resonator, IQPair(Square(1.0, 120), Square(0.0, 120)), IQPair(Square(1.0, 120), Square(0.0, 120)))

    with (
        patch.object(Bus, "upload_qpysequence") as upload,
        patch.object(Bus, "run") as run,
        patch.object(Bus, "acquire_qprogram_results") as acquire,
        patch.object(QbloxModule, "sync_sequencer"),
        patch.object(QbloxModule, "desync_sequencer"),
    ):
        acquire.return_value = [_IQResult(np.array([1.5, 2.5]))]
        result = platform.execute(qp)

    assert upload.call_count == 2  # drive + resonator
    assert run.call_count == 2
    assert acquire.call_count == 1  # only the readout bus
    assert [m.name for m in result.measurements] == ["resonator/m0"]
    iq = result.get(measurement=0)
    assert iq.dims == ("IQ",)
    assert iq.values.tolist() == [1.5, 2.5]


# --------------------------------------------------------------------------- deferred-feature coverage


def test_executor_software_parallel_axis(schema, refs, caps, runcard_schema):
    """A software ``Parallel`` co-sweeps its loops as ONE result axis named ``"a|b"`` with both coords."""
    drive, ro, w = _waveforms()
    qp = QProgram(schema=schema)
    a = qp.variable("a")
    b = qp.variable("b")
    with qp.for_loop(a, 0.0, 1.0, 0.5) | qp.for_loop(b, 10.0, 12.0, 1.0):  # 3 co-swept software points
        qp.set_parameter("drive_q0", "frequency", a)  # forces the parallel to software
        with qp.average(50):
            amp = qp.variable("amp")
            with qp.for_loop(amp, 0.0, 1.0, 0.2):  # 6 hardware points
                qp.set_gain(refs["drive_q0"], amp)
                qp.play(refs["drive_q0"], drive)
                qp.measure(refs["readout_q0"], ro, w)
    _, plan = validate(qp, caps)
    assert_sw_outer_hw_inner(qp, plan)
    platform = FakePlatform()
    result = QProgramExecutor(platform, qp, plan, runcard_schema).execute()
    data = result.measurements[0].data
    assert data.dims == ("a|b", "amp", "IQ")
    assert data.shape == (3, 6, 2)
    assert list(data.coords["a"].values) == [0.0, 0.5, 1.0]
    assert list(data.coords["b"].values) == [10.0, 11.0, 12.0]
    assert not np.isnan(data.values).any()
    assert len(platform.set_calls) == 3  # one set_parameter per co-swept point


def test_get_parameter_dataflow_same_iteration(schema, caps, runcard_schema):
    """A Variable produced by ``get_parameter`` is threaded into a later ``set_parameter`` host-side."""
    qp = QProgram(schema=schema)
    measured = qp.get_parameter("readout_q0", "frequency")
    qp.set_parameter("drive_q0", "frequency", measured)
    _, plan = validate(qp, caps)
    platform = FakePlatform()
    platform.get_value = 7.5
    QProgramExecutor(platform, qp, plan, runcard_schema).execute()
    assert any(value == 7.5 for _alias, _param, value, _channel in platform.set_calls)


def test_executor_state_and_raw_return_tokens(schema, refs, caps, runcard_schema):
    """``returns=("iq","state","raw")`` produces one field per token with the documented dims."""
    drive, ro, w = _waveforms()
    qp = QProgram(schema=schema)
    with qp.average(50):
        qp.play(refs["drive_q0"], drive)
        qp.measure(refs["readout_q0"], ro, w, returns=("iq", "state", "raw"))
    _, plan = validate(qp, caps)
    result = QProgramExecutor(FakePlatform(), qp, plan, runcard_schema).execute()
    measurement = result.measurements[0]
    assert set(measurement.fields) == {"iq", "state", "raw"}
    assert measurement.fields["iq"].dims == ("IQ",)
    assert measurement.fields["state"].dims == ()
    assert measurement.fields["raw"].dims == ("time", "IQ")
    assert measurement.fields["raw"].shape == (_RAW_SAMPLES, 2)
    # primary data is the iq field
    assert measurement.data.dims == ("IQ",)


def test_platform_execute_with_flux_qdac():
    """Full ``Platform.execute`` with a software-only flux (QDAC) op + a Qblox hardware frontier.

    Verifies: the flux ``set_offset`` validates + passes the SW/HW partition (it is a software-region
    leaf op, not a bare hardware op); the executor skips it during the software walk (it is armed by
    the up-front QDAC compile); and the QDAC start/stop is coordinated around the Qblox run.
    """
    from unittest.mock import MagicMock, patch
    from types import SimpleNamespace

    from qililab.data_management import build_platform
    from qililab.instruments.qblox import QbloxModule
    from qililab.platform.components.bus import Bus

    platform = build_platform(runcard="tests/runcards/qblox_and_qdac.yml")
    drive = platform.bus_ref("drive")
    resonator = platform.bus_ref("resonator")
    flux = platform.bus_ref("qdac_bus_1")

    qp = QProgram(schema=platform.bus_schema())
    qp.qdac.set_offset(flux, 0.25)  # static flux bias — software-only op in the outer region
    with qp.average(100):
        qp.play(drive, IQPair(Square(1.0, 40), Square(0.0, 40)))
        qp.measure(resonator, IQPair(Square(1.0, 120), Square(0.0, 120)), IQPair(Square(1.0, 120), Square(0.0, 120)))

    fake_qdac = MagicMock()
    fake_qdac_output = SimpleNamespace(qdacs=[fake_qdac], trigger_position="front")

    with (
        patch.object(Bus, "upload_qpysequence"),
        patch.object(Bus, "run") as run,
        patch.object(Bus, "acquire_qprogram_results") as acquire,
        patch.object(QbloxModule, "sync_sequencer"),
        patch.object(QbloxModule, "desync_sequencer"),
        patch.object(type(platform), "_compile_qdac_v2", return_value=fake_qdac_output),
    ):
        acquire.return_value = [_IQResult(np.array([0.1, 0.2]))]
        result = platform.execute(qp)

    # The Qblox frontier still ran and produced the measurement (flux op did not derail the walk).
    assert run.call_count == 2  # drive + resonator
    assert [m.name for m in result.measurements] == ["resonator/m0"]
    # QDAC was coordinated around the run: digital trace cleared, then started ("front" => after run).
    fake_qdac.remove_digital_trace.assert_called_once()
    fake_qdac.start.assert_called_once()


# --------------------------------------------------------------------------- qililab vendor: set_crosstalk


def test_qililab_vendor_set_crosstalk_is_software(schema, refs, caps, runcard_schema):
    """``program.qililab.set_crosstalk`` is a bus-less, software-only vendor op.

    Crosstalk is a qililab-only concern — the core ``qprogram`` package has no ``SetCrosstalk`` /
    ``CrosstalkMatrix``. The op classifies to software, passes the SW-outer / HW-inner partition, and
    the executor records the matrix on the platform (the deep flux compensation is applied separately).
    """
    from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix

    drive, ro, w = _waveforms()
    xtalk = CrosstalkMatrix()
    xtalk.matrix = {"readout_q0": {"readout_q0": 1.0}}

    qp = QProgram(schema=schema)
    qp.qililab.set_crosstalk(xtalk)  # vendor op (program.qililab.*)
    with qp.average(50):
        a = qp.variable("amp")
        with qp.for_loop(a, 0.0, 1.0, 0.2):
            qp.play(refs["drive_q0"], drive)
            qp.measure(refs["readout_q0"], ro, w)

    diagnostics, plan = validate(qp, caps)
    assert [d for d in diagnostics if d.severity == "error"] == []
    set_crosstalk_op = qp.body.elements[0]
    assert plan[set_crosstalk_op] == frozenset({"sw"})  # bus-less software op
    assert_sw_outer_hw_inner(qp, plan)  # software op + hardware frontier: legal

    platform = FakePlatform()
    QProgramExecutor(platform, qp, plan, runcard_schema).execute()
    assert platform.crosstalk_calls == [xtalk]  # matrix recorded on the platform
