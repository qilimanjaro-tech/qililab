"""Tests for the new-AST QDAC compiler (``qililab.qprogram.v2.qdac_compiler``).

The QDAC compiler programs the instruments as a side effect, so — like the legacy
``tests/qprogram/test_qdac_compiler.py`` — the QDAC-II instrument is a ``MagicMock(spec=QDevilQDac2)``
and the buses are lightweight stand-ins exposing ``alias`` / ``channels`` / ``instruments``.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import qprogram_qdac  # noqa: F401  (registers the qdac vendor namespace)
from qprogram import QProgram
from qprogram.buses import BusNaming, BusSchema
from qprogram.waveforms import Ramp

from qililab.instruments.qdevil.qdevil_qdac2 import QDevilQDac2
from qililab.qprogram.qdac_compiler import QdacCompilationOutput
from qililab.qprogram.v2.qdac_compiler import QdacCompilerV2


def _qdac_instrument(trigger_sync: bool = True) -> MagicMock:
    inst = MagicMock(spec=QDevilQDac2)
    inst.trigger_sync = trigger_sync
    inst.out_trigger = 1
    inst.in_trigger = 1
    inst.device = MagicMock()
    inst.device.name = "qdac"
    inst.settings = SimpleNamespace(voltage=[0.0, 0.0, 0.0, 0.0])
    inst._cache_dc = {}
    return inst


def _fake_bus(alias: str, channel: int, instrument: MagicMock) -> SimpleNamespace:
    return SimpleNamespace(alias=alias, channels=[channel], instruments=[instrument])


@pytest.fixture
def schema() -> BusSchema:
    s = BusSchema(naming=BusNaming("{element}"))
    s.add_element("flux1", {"flux": ("single", False)})
    return s


@pytest.fixture
def flux_ref(schema):
    return getattr(schema, "flux1")[0].flux


def test_set_offset_sets_voltage(schema, flux_ref):
    inst = _qdac_instrument()
    bus = _fake_bus("flux1", 1, inst)
    qp = QProgram(schema=schema)
    qp.qdac.set_offset(flux_ref, 0.3)

    QdacCompilerV2().compile(qp, qdacs=[inst], qdac_buses=[bus], qdac_offsets=[0.0])

    inst.set_parameter.assert_called_once()
    _, kwargs = inst.set_parameter.call_args
    assert kwargs["value"] == 0.3
    assert kwargs["channel_id"] == 1


def test_play_uploads_voltage_list_with_loop_repetitions(schema, flux_ref):
    inst = _qdac_instrument()
    bus = _fake_bus("flux1", 1, inst)
    qp = QProgram(schema=schema)
    v = qp.variable("v")
    with qp.for_loop(v, 0.0, 1.0, 0.25):
        qp.qdac.play(flux_ref, Ramp(from_amplitude=0.0, to_amplitude=1.0, duration=100), dwell=5, delay=2)

    out = QdacCompilerV2().compile(qp, qdacs=[inst], qdac_buses=[bus], qdac_offsets=[0.0])

    inst.upload_voltage_list.assert_called_once()
    _, kwargs = inst.upload_voltage_list.call_args
    assert kwargs["channel_id"] == 1
    assert kwargs["dwell_us"] == 5
    assert kwargs["sync_delay_s"] == 2
    expected_reps = QdacCompilerV2._calculate_iterations(0.0, 1.0, 0.25) + 1
    assert kwargs["repetitions"] == expected_reps
    assert isinstance(out, QdacCompilationOutput)
    assert out.trigger_position is None


def test_set_trigger_external_marks_front_position(schema, flux_ref):
    inst = _qdac_instrument(trigger_sync=True)
    bus = _fake_bus("flux1", 1, inst)
    qp = QProgram(schema=schema)
    qp.qdac.play(flux_ref, Ramp(from_amplitude=0.0, to_amplitude=1.0, duration=100))
    qp.qdac.set_trigger(flux_ref, duration=100, position="end", outputs=[1])

    out = QdacCompilerV2().compile(qp, qdacs=[inst], qdac_buses=[bus], qdac_offsets=[0.0])

    inst.set_end_marker_external_trigger.assert_called_once()
    assert out.trigger_position == "front"


def test_wait_trigger_external_marks_back_position(schema, flux_ref):
    inst = _qdac_instrument()
    bus = _fake_bus("flux1", 1, inst)
    qp = QProgram(schema=schema)
    qp.qdac.wait_trigger(flux_ref, port=2)

    out = QdacCompilerV2().compile(qp, qdacs=[inst], qdac_buses=[bus], qdac_offsets=[0.0])

    inst.set_in_external_trigger.assert_called_once_with(channel_id=1, in_port=2)
    assert out.trigger_position == "back"


def test_set_trigger_without_trigger_sync_raises(schema, flux_ref):
    inst = _qdac_instrument(trigger_sync=False)
    bus = _fake_bus("flux1", 1, inst)
    qp = QProgram(schema=schema)
    qp.qdac.play(flux_ref, Ramp(from_amplitude=0.0, to_amplitude=1.0, duration=100))
    qp.qdac.set_trigger(flux_ref, duration=100, position="start", outputs=[1])

    with pytest.raises(ValueError, match="trigger_sync"):
        QdacCompilerV2().compile(qp, qdacs=[inst], qdac_buses=[bus], qdac_offsets=[0.0])


def test_rf_op_on_qdac_bus_is_rejected(schema, flux_ref):
    inst = _qdac_instrument()
    bus = _fake_bus("flux1", 1, inst)
    qp = QProgram(schema=schema)
    qp.set_frequency(flux_ref, 5e9)

    with pytest.raises(NotImplementedError):
        QdacCompilerV2().compile(qp, qdacs=[inst], qdac_buses=[bus], qdac_offsets=[0.0])
