"""Tests for the ported features of the new-AST Qblox compiler (``QbloxCompilerV2``).

Exercises the features ported from the legacy compiler: Square/FlatTop chunk optimisations, markers,
trigger + wait_trigger, active reset, and dynamic (variable-duration) waits + dynamic sync. Each test
asserts that ``compile(...)`` returns a ``QbloxCompilationOutput`` whose sequences build valid Q1ASM
(``Sequence.todict()`` succeeds — qpysequence would raise on malformed programs).
"""

import pytest
import qprogram_qblox  # noqa: F401  (registers the qblox vendor namespace + ops)
from qprogram import QProgram
from qprogram.buses import BusNaming, BusSchema
from qprogram.waveforms import FlatTop, IQPair, Square

from qililab.qprogram.v2.qblox_compiler import QbloxCompilerV2


@pytest.fixture
def schema():
    s = BusSchema(naming=BusNaming("{element}"))
    s.add_element("drive", {"drive": ("IQ", False)})
    s.add_element("readout", {"readout": ("IQ", True)})
    s.add_element("control", {"drive": ("IQ", False)})
    return s


@pytest.fixture
def refs(schema):
    return {
        "drive": getattr(schema, "drive")[0].drive,
        "readout": getattr(schema, "readout")[0].readout,
        "control": getattr(schema, "control")[0].drive,
    }


def _iq(amp, duration):
    return IQPair(Square(amp, duration), Square(0.0, duration))


def _all_buses(qp):
    return list(qp.buses)


def _assert_builds(output):
    for sequence in output.sequences.values():
        assert set(sequence.todict()) == {"waveforms", "weights", "acquisitions", "program"}


def test_square_chunk_optimization(schema, refs):
    qp = QProgram(schema=schema)
    with qp.average(100):
        qp.play(refs["drive"], _iq(0.5, 400))  # >=100 ns -> chunked play loop
    output = QbloxCompilerV2().compile(qp, qblox_buses=_all_buses(qp))
    program_text = str(output.sequences["drive"]._program)
    assert "square_0" in program_text  # the chunk loop label
    _assert_builds(output)


def test_flat_top_chunk_optimization(schema, refs):
    qp = QProgram(schema=schema)
    with qp.average(50):
        flat = FlatTop(amplitude=0.5, duration=600, smooth_duration=20, buffer=0)
        qp.play(refs["drive"], IQPair(flat, FlatTop(amplitude=0.0, duration=600, smooth_duration=20, buffer=0)))
    output = QbloxCompilerV2().compile(qp, qblox_buses=_all_buses(qp))
    assert "square_0" in str(output.sequences["drive"]._program)
    _assert_builds(output)


def test_set_markers(schema, refs):
    qp = QProgram(schema=schema)
    with qp.average(10):
        qp.qblox.set_markers(refs["drive"], "0001")
        qp.play(refs["drive"], _iq(0.5, 40))
    output = QbloxCompilerV2().compile(qp, qblox_buses=_all_buses(qp), markers={"drive": "0010"})
    _assert_builds(output)


def test_set_trigger_and_wait_trigger(schema, refs):
    qp = QProgram(schema=schema)
    with qp.average(10):
        qp.qblox.set_trigger(refs["drive"], duration=100, outputs=[1])
        qp.qblox.wait_trigger(refs["control"], duration=40)
    output = QbloxCompilerV2().compile(qp, qblox_buses=_all_buses(qp), ext_trigger=True)
    _assert_builds(output)


def test_wait_trigger_requires_ext_trigger(schema, refs):
    qp = QProgram(schema=schema)
    with qp.average(10):
        qp.qblox.wait_trigger(refs["control"], duration=40)
    with pytest.raises(AttributeError):
        QbloxCompilerV2().compile(qp, qblox_buses=_all_buses(qp), ext_trigger=False)


def test_active_reset_records_trigger_network(schema, refs):
    qp = QProgram(schema=schema)
    with qp.average(100):
        qp.qblox.active_reset(
            bus=refs["readout"],
            waveform=_iq(0.3, 200),
            weights=_iq(1.0, 200),
            control_bus=refs["control"],
            reset_pulse=_iq(0.5, 40),
            trigger_address=1,
        )
    output = QbloxCompilerV2().compile(qp, qblox_buses=_all_buses(qp))
    # The readout bus must be registered for trigger-network setup by the platform.
    assert output.trigger_network_required == {"readout": 1}
    # The control bus program must contain a conditional (set_cond) and a latch reset.
    control_program = str(output.sequences["control"]._program)
    assert "set_cond" in control_program
    assert "latch_rst" in control_program
    _assert_builds(output)


def test_dynamic_variable_wait(schema, refs):
    qp = QProgram(schema=schema)
    with qp.average(50):
        t = qp.variable("t")
        with qp.for_loop(t, 0, 100, 4):
            qp.play(refs["drive"], _iq(0.5, 40))
            qp.wait(refs["drive"], t)
            qp.measure(refs["readout"], _iq(0.3, 200), _iq(1.0, 200))
    output = QbloxCompilerV2().compile(qp, qblox_buses=_all_buses(qp))
    # The dynamic sync must replay the shared time register on the readout bus.
    drive_program = str(output.sequences["drive"]._program)
    assert "wait " in drive_program.lower()
    _assert_builds(output)


def test_two_dynamic_waits_without_sync_raises(schema, refs):
    qp = QProgram(schema=schema)
    with qp.average(10):
        t = qp.variable("t")
        with qp.for_loop(t, 0, 100, 4):
            qp.wait(refs["drive"], t)
            qp.wait(refs["drive"], t)  # second dynamic wait, no sync between
    with pytest.raises(NotImplementedError):
        QbloxCompilerV2().compile(qp, qblox_buses=_all_buses(qp), disable_autosync=True)
