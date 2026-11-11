import re

import numpy as np
import pytest
from qprogram import ValidationError
from qprogram.operations import Play

from qililab import Calibration, IQDrag, IQPair, QProgram, Square
from qililab.exceptions import VariableAllocated
from qililab.qprogram.prepass.shared_prepass import prepare_shared

WEIGHTS = IQPair(I=Square(amplitude=1.0, duration=100), Q=Square(amplitude=0.0, duration=100))


class TestPrepareShared:
    def test_bus_mapping_and_calibration_are_applied(self):
        calibration = Calibration()
        calibration.add_waveform(bus="drive_q0", name="Xpi", waveform=Square(amplitude=1.0, duration=40))
        qp = QProgram()
        qp.play(bus="drive", waveform="Xpi")

        prepared = prepare_shared(qp, bus_mapping={"drive": "drive_q0"}, calibration=calibration)

        assert prepared.buses == {"drive_q0"}
        (play,) = prepared.body.elements
        assert isinstance(play, Play)
        assert play.bus == "drive_q0"
        np.testing.assert_array_equal(play.waveform.envelope(), np.ones(40))
        assert qp.buses == {"drive"}

    def test_unmapped_named_operation_raises_error(self):
        qp = QProgram()
        qp.play(bus="drive", waveform="Xpi")
        calibration = Calibration()

        with pytest.raises(RuntimeError, match="contains named operations that are not mapped"):
            prepare_shared(qp, bus_mapping={"drive": "drive_q0"}, calibration=calibration)

    def test_wait_trigger_then_if_trigger_raises_error(self):
        qp = QProgram()
        qp.qblox.wait_trigger(bus="drive", duration=100)
        with qp.if_trigger(expected_wait_time_ns=2252):
            qp.wait(bus="readout", duration=100)

        with pytest.raises(
            NotImplementedError,
            match=re.escape("if_trigger() cannot be used together with wait_trigger in the same QProgram."),
        ):
            prepare_shared(qp)

    def test_if_trigger_then_qdac_wait_trigger_raises_error(self):
        qp = QProgram()
        with qp.if_trigger(expected_wait_time_ns=2252):
            qp.wait(bus="readout", duration=100)
        qp.qdac.wait_trigger(bus="flux", port=1)

        with pytest.raises(
            NotImplementedError,
            match=re.escape("if_trigger() cannot be used together with wait_trigger in the same QProgram."),
        ):
            prepare_shared(qp)

    def test_measure_reset_and_if_trigger_raises_error(self):
        qp = QProgram()
        qp.qblox.measure_reset(
            bus="readout",
            waveform=IQPair(I=Square(1.0, 1000), Q=Square(0.0, 1000)),
            weights=WEIGHTS,
            control_bus="drive",
            reset_pulse=IQDrag(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5),
        )
        with qp.if_trigger(expected_wait_time_ns=2252):
            qp.wait(bus="readout", duration=100)

        with pytest.raises(
            NotImplementedError,
            match=re.escape(
                "if_trigger() cannot be used together with qp.qblox.measure_reset() in the same QProgram."
            ),
        ):
            prepare_shared(qp)

    def test_nested_loops_on_one_variable_raises_error(self):
        """The builder refuses an inner loop over the variable of an enclosing one; the pre-pass also checks the
        programs the builder didn't build, such as ones read from .qp."""
        qp = QProgram()
        x = qp.variable("x")
        with qp.sweep(x).from_range(0, 10, 1):
            inner = qp.sweep(x).from_range(100, 110, 1)
            with pytest.raises(VariableAllocated):
                with inner:
                    pass

        text = """#!QProgram 0.3

body:
  var x

  for x in Range(start=0.0, stop=10.0, step=1.0):
    for x in Range(start=100.0, stop=110.0, step=1.0):
      wait "drive" 100
"""
        with pytest.raises(VariableAllocated):
            prepare_shared(QProgram.from_qp(text))

    def test_disable_autosync_inside_a_block_raises_error(self):
        """qp.qblox.disable_autosync only ever puts it at the top of the body; a .qp file could put it elsewhere."""
        text = """#!QProgram 0.3

require qililab 0.1

body:
  average 10:
    qililab.disable_autosync
    wait "drive" 100
"""
        with pytest.raises(ValueError, match="qililab.disable_autosync applies to the whole program"):
            prepare_shared(QProgram.from_qp(text))

    @pytest.mark.parametrize(
        "expression, code",
        [
            (lambda g, h: g + h + h, "qililab.unsupported-arithmetic"),
            (lambda g, h: g * 2, "qililab.unsupported-arithmetic"),
            (lambda g, h: 2 / g, "qililab.unsupported-arithmetic"),
            (lambda g, h: g * h, "qililab.unsupported-arithmetic"),
            (lambda g, h: g > 0.5, "qililab.unsupported-arithmetic"),
            (lambda g, h: abs(g), "qililab.unsupported-arithmetic"),
        ],
        ids=["two-additions", "multiplication", "division", "product-of-variables", "comparison", "abs"],
    )
    def test_unsupported_arithmetic_raises_validation_error(self, expression, code):
        """An expression qililab can't compile is rejected: anything beyond one + or - between a variable and a
        constant or another variable, or a negated variable."""
        qp = QProgram()
        g = qp.variable("g")
        h = qp.variable("h")
        with qp.sweep(g).from_range(0.0, 1.0, 0.5):
            with qp.sweep(h).from_range(0.0, 1.0, 0.5):
                qp.set_gain(bus="drive", gain=expression(g, h))

        with pytest.raises(ValidationError, match=re.escape(code)):
            prepare_shared(qp)

    def test_unsupported_feature_raises_validation_error(self):
        """Anything outside qililab's capability profile fails here, e.g. a sweep over explicit values."""
        qp = QProgram()
        x = qp.variable("x")
        with qp.sweep(x).from_values([1.0, 2.0, 5.0]):
            qp.set_gain(bus="drive", gain=x)

        with pytest.raises(ValidationError, match="The QProgram uses features qililab does not support"):
            prepare_shared(qp)
