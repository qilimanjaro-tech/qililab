"""Tests for the new-AST flux-crosstalk compensation lowering (``qililab.qprogram.v2.crosstalk``).

The transform is a static, deep-copying AST rewrite that injects crosstalk-compensated flux ops. It
reuses the same :class:`~qililab.qprogram.crosstalk_matrix.CrosstalkMatrix` /
:class:`~qililab.qprogram.flux_vector.FluxVector` math as the legacy
``QProgram.with_crosstalk_qblox`` / ``with_crosstalk_qdac`` methods, so the strongest tests here build
an equivalent **legacy** QProgram, run the legacy lowering, and assert the new transform produces
numerically identical compensated offsets / gains / waveforms.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import qprogram_qblox  # noqa: F401  (registers the qblox vendor namespace + profile)
import qprogram_qdac  # noqa: F401  (registers the qdac vendor namespace + profile)
from qprogram import QProgram
from qprogram.buses import BusNaming, BusSchema
from qprogram.operations import Play, SetGain, SetOffset
from qprogram.waveforms import Arbitrary, IQPair, Ramp, Square
from qprogram_qdac.operations import Play as QdacPlay
from qprogram_qdac.operations import SetOffset as QdacSetOffset

import qililab.qprogram.v2  # noqa: F401  (registers the qililab vendor namespace)
from qililab.core.variables import Domain
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix, NonLinearCrosstalkMatrix
from qililab.qprogram.flux_vector import FluxVector
from qililab.qprogram.operations import Play as LegacyPlay
from qililab.qprogram.operations import SetGain as LegacySetGain
from qililab.qprogram.operations import SetOffset as LegacySetOffset
from qililab.qprogram.qprogram import QProgram as LegacyQProgram
from qililab.qprogram.v2.crosstalk import apply_crosstalk_compensation, extract_crosstalk
from qililab.qprogram.v2.vendor import SetCrosstalk
from qililab.waveforms import Arbitrary as LegacyArbitrary
from qililab.waveforms import IQPair as LegacyIQPair
from qililab.waveforms import Square as LegacySquare

# --------------------------------------------------------------------------- fixtures


@pytest.fixture
def schema() -> BusSchema:
    s = BusSchema(naming=BusNaming("{element}"))
    s.add_element("flux1", {"flux": ("single", False)})
    s.add_element("flux2", {"flux": ("single", False)})
    s.add_element("drive", {"drive": ("IQ", False)})
    s.add_element("readout", {"readout": ("IQ", True)})
    return s


@pytest.fixture
def flux_refs(schema):
    return {
        "flux1": getattr(schema, "flux1")[0].flux,
        "flux2": getattr(schema, "flux2")[0].flux,
        "drive": getattr(schema, "drive")[0].drive,
        "readout": getattr(schema, "readout")[0].readout,
    }


def _linear_matrix() -> CrosstalkMatrix:
    inv = np.linalg.inv([[1, 0.5], [0.5, 1]])
    return CrosstalkMatrix().from_array(["flux1", "flux2"], inv)


def _nonlinear_matrix() -> NonLinearCrosstalkMatrix:
    nl = NonLinearCrosstalkMatrix.from_linear(_linear_matrix())
    nl.set_non_linear_params("flux2", "flux1", beta_c=0.8, amplitude=0.5)
    return nl


# --------------------------------------------------------------------------- extract_crosstalk


def test_extract_crosstalk_returns_matrix(schema, flux_refs):
    ct = _linear_matrix()
    qp = QProgram(schema=schema)
    qp.qililab.set_crosstalk(ct)
    qp.set_offset(flux_refs["flux1"], 0.2)

    assert extract_crosstalk(qp) is ct


def test_extract_crosstalk_none_when_absent(schema, flux_refs):
    qp = QProgram(schema=schema)
    qp.set_offset(flux_refs["flux1"], 0.2)

    assert extract_crosstalk(qp) is None


def test_extract_crosstalk_finds_op_inside_block(schema, flux_refs):
    ct = _linear_matrix()
    qp = QProgram(schema=schema)
    with qp.average(10):
        qp.qililab.set_crosstalk(ct)
        qp.set_offset(flux_refs["flux1"], 0.2)

    assert extract_crosstalk(qp) is ct


# --------------------------------------------------------------------------- general behaviour


def test_apply_is_non_mutating(schema, flux_refs):
    ct = _linear_matrix()
    qp = QProgram(schema=schema)
    qp.qililab.set_crosstalk(ct)
    qp.set_offset(flux_refs["flux1"], 0.2)

    n_before = len(qp.body.elements)
    apply_crosstalk_compensation(qp, ct)
    # Input untouched: still has its original set_crosstalk + set_offset.
    assert len(qp.body.elements) == n_before
    assert isinstance(qp.body.elements[0], SetCrosstalk)


def test_set_crosstalk_op_is_stripped(schema, flux_refs):
    ct = _linear_matrix()
    qp = QProgram(schema=schema)
    qp.qililab.set_crosstalk(ct)
    qp.set_offset(flux_refs["flux1"], 0.2)

    out = apply_crosstalk_compensation(qp, ct)
    assert not any(isinstance(e, SetCrosstalk) for e in out.body.elements)


def test_no_flux_ops_is_noop(schema, flux_refs):
    """A program with a crosstalk matrix but no flux ops on crosstalk buses is returned unchanged."""
    ct = _linear_matrix()
    qp = QProgram(schema=schema)
    qp.qililab.set_crosstalk(ct)
    qp.play(flux_refs["drive"], qprogram_iq())  # not a crosstalk bus

    out = apply_crosstalk_compensation(qp, ct)
    # Only the drive play remains (set_crosstalk stripped, no flux compensation injected).
    assert len(out.body.elements) == 1
    assert out.body.elements[0].bus == "drive"


def test_active_reset_rejected(schema, flux_refs):
    """``qblox.active_reset`` is incompatible with crosstalk compensation (legacy parity)."""
    ct = _linear_matrix()
    weights = qprogram_iq()
    qp = QProgram(schema=schema)
    qp.qililab.set_crosstalk(ct)
    qp.set_offset(flux_refs["flux1"], 0.2)
    qp.qblox.active_reset(
        bus="readout",
        waveform=weights,
        weights=weights,
        control_bus="drive",
        reset_pulse=weights,
    )

    with pytest.raises(TypeError, match="active_reset"):
        apply_crosstalk_compensation(qp, ct)


def test_mixed_flux_families_rejected(schema, flux_refs):
    """A program cannot mix core (qblox) and qdac flux ops on the same crosstalk buses."""
    ct = _linear_matrix()
    qp = QProgram(schema=schema)
    qp.qililab.set_crosstalk(ct)
    qp.set_offset(flux_refs["flux1"], 0.2)  # core op
    qp.qdac.set_offset(flux_refs["flux2"], 0.1)  # qdac vendor op

    with pytest.raises(ValueError, match="mix"):
        apply_crosstalk_compensation(qp, ct)


def qprogram_iq() -> IQPair:
    return IQPair(Square(0.1, 50), Square(0.1, 50))


# --------------------------------------------------------------------------- linear (qblox core ops)


def test_linear_scalar_offset(schema, flux_refs):
    ct = _linear_matrix()
    qp = QProgram(schema=schema)
    qp.qililab.set_crosstalk(ct)
    qp.set_offset(flux_refs["flux1"], 0.2)
    qp.set_offset(flux_refs["flux2"], 0.1)

    out = apply_crosstalk_compensation(qp, ct)
    offsets = {e.bus: float(e.offset_path0) for e in out.body.elements if isinstance(e, SetOffset)}
    expected = ct.flux_to_bias({"flux1": 0.2, "flux2": 0.1})
    assert math.isclose(offsets["flux1"], float(expected["flux1"]))
    assert math.isclose(offsets["flux2"], float(expected["flux2"]))


def test_linear_scalar_gain(schema, flux_refs):
    ct = _linear_matrix()
    qp = QProgram(schema=schema)
    qp.qililab.set_crosstalk(ct)
    qp.set_gain(flux_refs["flux1"], 0.3)
    qp.set_gain(flux_refs["flux2"], 0.0)

    out = apply_crosstalk_compensation(qp, ct)
    gains = {e.bus: float(e.gain) for e in out.body.elements if isinstance(e, SetGain)}
    expected = ct.flux_to_bias({"flux1": 0.3, "flux2": 0.0})
    assert math.isclose(gains["flux1"], float(expected["flux1"]))
    assert math.isclose(gains["flux2"], float(expected["flux2"]))


def test_linear_play_injects_arbitrary_per_bus(schema, flux_refs):
    ct = _linear_matrix()
    qp = QProgram(schema=schema)
    qp.qililab.set_crosstalk(ct)
    qp.play(flux_refs["flux1"], Square(0.1, 5))

    out = apply_crosstalk_compensation(qp, ct)
    plays = {e.bus: e for e in out.body.elements if isinstance(e, Play)}
    assert set(plays) == {"flux1", "flux2"}
    expected = ct.flux_to_bias({"flux1": np.full(5, 0.1), "flux2": np.zeros(5)})
    assert isinstance(plays["flux1"].waveform, Arbitrary)
    assert np.allclose(plays["flux1"].waveform.envelope(), expected["flux1"])
    assert np.allclose(plays["flux2"].waveform.envelope(), expected["flux2"])


# --------------------------------------------------------------------------- qdac vendor flux family


def test_qdac_scalar_offset(schema, flux_refs):
    ct = _linear_matrix()
    qp = QProgram(schema=schema)
    qp.qililab.set_crosstalk(ct)
    qp.qdac.set_offset(flux_refs["flux1"], 0.2)
    qp.qdac.set_offset(flux_refs["flux2"], 0.1)

    out = apply_crosstalk_compensation(qp, ct)
    offsets = {e.bus: float(e.offset) for e in out.body.elements if isinstance(e, QdacSetOffset)}
    assert set(offsets) == {"flux1", "flux2"}

    # Legacy semantics: set_crosstalk_from_bias (resting bias 0) then accumulate target flux.
    fv = FluxVector()
    fv.set_crosstalk_from_bias(ct, {"flux1": 0.0, "flux2": 0.0})
    fv.flux_vector["flux1"] = 0.2
    fv.flux_vector["flux2"] = 0.1
    fv.update_bias_vector()
    assert math.isclose(offsets["flux1"], float(fv.bias_vector["flux1"]))
    assert math.isclose(offsets["flux2"], float(fv.bias_vector["flux2"]))


def test_qdac_play_preserves_timing(schema, flux_refs):
    ct = _linear_matrix()
    qp = QProgram(schema=schema)
    qp.qililab.set_crosstalk(ct)
    qp.qdac.play(flux_refs["flux1"], Ramp(from_amplitude=0.0, to_amplitude=0.1, duration=5), dwell=3, delay=1)

    out = apply_crosstalk_compensation(qp, ct)
    plays = {e.bus: e for e in out.body.elements if isinstance(e, QdacPlay)}
    assert set(plays) == {"flux1", "flux2"}
    for play in plays.values():
        assert isinstance(play.waveform, Arbitrary)
        assert play.dwell == 3
        assert play.delay == 1
    # flux1 carries the ramp envelope through the matrix; flux2 its crosstalk-induced compensation.
    fv = FluxVector()
    fv.set_crosstalk_from_bias(ct, {"flux1": 0.0, "flux2": 0.0})
    fv.flux_vector["flux1"] = Ramp(from_amplitude=0.0, to_amplitude=0.1, duration=5).envelope()
    fv.update_bias_vector()
    assert np.allclose(plays["flux1"].waveform.envelope(), np.asarray(fv.bias_vector["flux1"]))
    assert np.allclose(plays["flux2"].waveform.envelope(), np.asarray(fv.bias_vector["flux2"]))


# --------------------------------------------------------------------------- non-linear: legacy parity


def _play_value(element):
    """Normalise a ``Play`` op to ``("Play", bus, kind, amplitude | None, samples | None)``.

    For a single-channel waveform we capture either its (constant) amplitude or its full envelope; for
    an IQ waveform (e.g. on a non-flux drive bus) we only compare bus + kind.
    """
    waveform = element.waveform
    amp = getattr(waveform, "amplitude", None)
    env = None
    if amp is None and hasattr(waveform, "envelope") and not type(waveform).__name__.startswith("IQ"):
        try:
            env = tuple(np.round(np.asarray(waveform.envelope()), 8).tolist())
        except (AttributeError, TypeError):
            env = None
    return ("Play", element.bus, type(waveform).__name__, None if amp is None else float(amp), env)


def _new_value(element):
    """Normalise a new-AST flux op to a comparable tuple."""
    if isinstance(element, SetOffset):
        return ("SetOffset", element.bus, float(element.offset_path0))
    if isinstance(element, SetGain):
        return ("SetGain", element.bus, float(element.gain))
    if isinstance(element, Play):
        return _play_value(element)
    return (type(element).__name__, getattr(element, "bus", "-"))


def _legacy_value(element):
    if isinstance(element, LegacySetOffset):
        return ("SetOffset", element.bus, float(element.offset_path0))
    if isinstance(element, LegacySetGain):
        return ("SetGain", element.bus, float(element.gain))
    if isinstance(element, LegacyPlay):
        return _play_value(element)
    return (type(element).__name__, getattr(element, "bus", "-"))


def _assert_flux_parity(legacy_elements, new_elements):
    """Assert the legacy-lowered and new-lowered programs agree element-by-element on flux ops."""
    assert len(legacy_elements) == len(new_elements), (
        f"length mismatch {len(legacy_elements)} vs {len(new_elements)}"
    )
    for i, (le, ne) in enumerate(zip(legacy_elements, new_elements)):
        lv, nv = _legacy_value(le), _new_value(ne)
        assert lv[0] == nv[0], f"[{i}] type {lv[0]} != {nv[0]}"
        if lv[0] in ("SetOffset", "SetGain"):
            assert lv[1] == nv[1], f"[{i}] bus {lv[1]} != {nv[1]}"
            assert math.isclose(lv[2], nv[2], abs_tol=1e-9), f"[{i}] value {lv[2]} != {nv[2]}"
        elif lv[0] == "Play":
            assert lv[1] == nv[1], f"[{i}] play bus {lv[1]} != {nv[1]}"
            assert lv[2] == nv[2], f"[{i}] waveform kind {lv[2]} != {nv[2]}"
            if lv[3] is not None and nv[3] is not None:
                assert math.isclose(lv[3], nv[3], abs_tol=1e-9), f"[{i}] amp {lv[3]} != {nv[3]}"
            if lv[4] is not None and nv[4] is not None:
                assert np.allclose(lv[4], nv[4], atol=1e-8), f"[{i}] samples differ"


def test_nonlinear_parity_basic(schema, flux_refs):
    """Non-linear compensation matches the legacy ``with_crosstalk_qblox`` numerically."""
    nl = _nonlinear_matrix()
    sq, sqiq = LegacySquare(0.1, 50), LegacyIQPair(LegacySquare(0.1, 50), LegacySquare(0.1, 50))
    legacy = LegacyQProgram()
    off = legacy.variable(label="offset", domain=Domain.Voltage)
    with legacy.for_loop(variable=off, start=0, stop=0.1, step=0.08):
        legacy.set_offset(bus="flux1", offset_path0=off)
        legacy.wait(bus="drive", duration=10)
        legacy.wait(bus="flux1", duration=10)
        legacy.wait(bus="flux2", duration=10)
        legacy.set_gain(bus="flux2", gain=0.05)
        legacy.play(bus="flux1", waveform=sq)
        legacy.play(bus="drive", waveform=sqiq)
        legacy.sync(["drive", "readout"])
        legacy.measure(bus="readout", waveform=sqiq, weights=sqiq)
    legacy_out = legacy.with_crosstalk_qblox(nl)

    nsq, nsqiq = Square(0.1, 50), qprogram_iq()
    qp = QProgram(schema=schema)
    noff = qp.variable("offset")
    qp.qililab.set_crosstalk(nl)
    with qp.for_loop(noff, 0.0, 0.1, 0.08):
        qp.set_offset(flux_refs["flux1"], noff)
        qp.wait(flux_refs["drive"], 10)
        qp.wait(flux_refs["flux1"], 10)
        qp.wait(flux_refs["flux2"], 10)
        qp.set_gain(flux_refs["flux2"], 0.05)
        qp.play(flux_refs["flux1"], nsq)
        qp.play(flux_refs["drive"], nsqiq)
        qp.sync(["drive", "readout"])
        qp.measure(flux_refs["readout"], nsqiq, nsqiq)
    new_out = apply_crosstalk_compensation(qp, nl)

    _assert_flux_parity(legacy_out.body.elements, new_out.body.elements)


def test_nonlinear_parity_arbitrary_play(schema, flux_refs):
    """Non-linear compensation of a non-constant flux pulse → ``Arbitrary`` per bus, gain 1."""
    nl = _nonlinear_matrix()
    # Use identical Arbitrary samples on both sides to isolate the crosstalk math from waveform impls.
    samples = (0.1 * np.exp(-np.linspace(-2, 2, 50) ** 2 / 2)).round(8)
    sqiq = LegacyIQPair(LegacySquare(0.1, 50), LegacySquare(0.1, 50))
    legacy = LegacyQProgram()
    legacy.play(bus="flux1", waveform=LegacyArbitrary(samples.copy()))
    legacy.play(bus="drive", waveform=sqiq)
    legacy.sync(["drive", "readout"])
    legacy.measure(bus="readout", waveform=sqiq, weights=sqiq)
    legacy_out = legacy.with_crosstalk_qblox(nl)

    nsqiq = qprogram_iq()
    qp = QProgram(schema=schema)
    qp.qililab.set_crosstalk(nl)
    qp.play(flux_refs["flux1"], Arbitrary(samples.copy()))
    qp.play(flux_refs["drive"], nsqiq)
    qp.sync(["drive", "readout"])
    qp.measure(flux_refs["readout"], nsqiq, nsqiq)
    new_out = apply_crosstalk_compensation(qp, nl)

    _assert_flux_parity(legacy_out.body.elements, new_out.body.elements)
    # Spot-check the expected shape: SetGain==1, SetOffset==0, Arbitrary play per crosstalk bus.
    assert isinstance(new_out.body.elements[0], SetGain)
    assert math.isclose(float(new_out.body.elements[0].gain), 1.0)
    assert isinstance(new_out.body.elements[2], Play)
    assert isinstance(new_out.body.elements[2].waveform, Arbitrary)


def test_nonlinear_parity_repeat_offset_play(schema, flux_refs):
    """Consecutive offsets / plays on the same bus repeat their compensated structure (legacy parity)."""
    nl = _nonlinear_matrix()
    sq, sqiq = LegacySquare(0.1, 50), LegacyIQPair(LegacySquare(0.1, 50), LegacySquare(0.1, 50))
    legacy = LegacyQProgram()
    off = legacy.variable(label="offset", domain=Domain.Voltage)
    with legacy.for_loop(variable=off, start=0, stop=0.1, step=0.08):
        legacy.set_offset(bus="flux1", offset_path0=off)
        legacy.wait(bus="drive", duration=10)
        legacy.wait(bus="flux1", duration=10)
        legacy.wait(bus="flux2", duration=10)
        legacy.set_offset(bus="flux1", offset_path0=0.1)
        legacy.wait(bus="drive", duration=10)
        legacy.wait(bus="flux1", duration=10)
        legacy.wait(bus="flux2", duration=10)
        legacy.play(bus="flux1", waveform=sq)
        legacy.play(bus="flux1", waveform=sq)
        legacy.play(bus="drive", waveform=sqiq)
        legacy.sync(["drive", "readout"])
        legacy.measure(bus="readout", waveform=sqiq, weights=sqiq)
    legacy_out = legacy.with_crosstalk_qblox(nl)

    nsq, nsqiq = Square(0.1, 50), qprogram_iq()
    qp = QProgram(schema=schema)
    noff = qp.variable("offset")
    qp.qililab.set_crosstalk(nl)
    with qp.for_loop(noff, 0.0, 0.1, 0.08):
        qp.set_offset(flux_refs["flux1"], noff)
        qp.wait(flux_refs["drive"], 10)
        qp.wait(flux_refs["flux1"], 10)
        qp.wait(flux_refs["flux2"], 10)
        qp.set_offset(flux_refs["flux1"], 0.1)
        qp.wait(flux_refs["drive"], 10)
        qp.wait(flux_refs["flux1"], 10)
        qp.wait(flux_refs["flux2"], 10)
        qp.play(flux_refs["flux1"], nsq)
        qp.play(flux_refs["flux1"], nsq)
        qp.play(flux_refs["drive"], nsqiq)
        qp.sync(["drive", "readout"])
        qp.measure(flux_refs["readout"], nsqiq, nsqiq)
    new_out = apply_crosstalk_compensation(qp, nl)

    _assert_flux_parity(legacy_out.body.elements, new_out.body.elements)


def test_nonlinear_parity_play_before_loop(schema, flux_refs):
    """A flux play outside the loop, then a swept loop — compensated identically to the legacy."""
    nl = _nonlinear_matrix()
    samples = (0.7 * np.exp(-np.linspace(-2, 2, 50) ** 2 / 2)).round(8)
    sqiq = LegacyIQPair(LegacySquare(0.1, 50), LegacySquare(0.1, 50))
    legacy = LegacyQProgram()
    off = legacy.variable(label="offset", domain=Domain.Voltage)
    legacy.play(bus="flux1", waveform=LegacyArbitrary(samples.copy()))
    legacy.sync()
    with legacy.for_loop(variable=off, start=0, stop=0.1, step=0.08):
        legacy.set_offset(bus="flux1", offset_path0=off)
        legacy.play(bus="flux1", waveform=LegacyArbitrary(samples.copy()))
        legacy.play(bus="drive", waveform=sqiq)
        legacy.sync(["drive", "readout"])
        legacy.measure(bus="readout", waveform=sqiq, weights=sqiq)
    legacy_out = legacy.with_crosstalk_qblox(nl)

    nsqiq = qprogram_iq()
    qp = QProgram(schema=schema)
    noff = qp.variable("offset")
    qp.qililab.set_crosstalk(nl)
    qp.play(flux_refs["flux1"], Arbitrary(samples.copy()))
    qp.sync()
    with qp.for_loop(noff, 0.0, 0.1, 0.08):
        qp.set_offset(flux_refs["flux1"], noff)
        qp.play(flux_refs["flux1"], Arbitrary(samples.copy()))
        qp.play(flux_refs["drive"], nsqiq)
        qp.sync(["drive", "readout"])
        qp.measure(flux_refs["readout"], nsqiq, nsqiq)
    new_out = apply_crosstalk_compensation(qp, nl)

    _assert_flux_parity(legacy_out.body.elements, new_out.body.elements)
