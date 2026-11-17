import re

import numpy as np
import pytest
from qprogram import ValidationError
from qprogram.operations import Play

from qililab import Calibration, IQDrag, IQPair, QProgram, Square
from qililab.exceptions import VariableAllocated
from qililab.qprogram.compilers.prepass.shared_prepass import prepare_shared

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
            match=re.escape("if_trigger() cannot be used together with qp.qblox.measure_reset() in the same QProgram."),
        ):
            prepare_shared(qp)

    def test_nested_loops_on_one_variable_raises_error(self):
        """The builder refuses an inner loop over the variable of an enclosing one, as qililab always did."""
        qp = QProgram()
        x = qp.variable("x")
        with qp.sweep(x).from_linspace(0, 10, 11):
            inner = qp.sweep(x).from_linspace(100, 110, 11)
            with pytest.raises(VariableAllocated):
                with inner:
                    pass

    def test_range_sweep_raises_error(self):
        """qililab's loops were linspaces: qprogram's from_range, which keeps the step, is refused."""
        qp = QProgram()
        x = qp.variable("x")
        with qp.sweep(x).from_range(0, 10, 1):
            qp.wait(bus="drive", duration=100)

        with pytest.raises(ValidationError, match="requires capability 'sweep.range'"):
            prepare_shared(qp)

    @pytest.mark.parametrize(
        "expression, code",
        [
            (lambda g, h: g + h + h, "qililab.unsupported-arithmetic"),
            (lambda g, h: g * 2, "qililab.unsupported-arithmetic"),
            (lambda g, h: 2 / g, "qililab.unsupported-arithmetic"),
            (lambda g, h: g * h, "qililab.unsupported-arithmetic"),
            (lambda g, h: g > 0.5, "qililab.unsupported-arithmetic"),
            (lambda g, h: abs(g), "qililab.unsupported-arithmetic"),
            (lambda g, h: +g, "qililab.unsupported-arithmetic"),
        ],
        ids=["two-additions", "multiplication", "division", "product-of-variables", "comparison", "abs", "unary-plus"],
    )
    def test_unsupported_arithmetic_raises_validation_error(self, expression, code):
        """An expression qililab can't compile is rejected: anything beyond one + or - between a variable and a
        constant or another variable, or a negated variable."""
        qp = QProgram()
        g = qp.variable("g")
        h = qp.variable("h")
        with qp.sweep(g).from_linspace(0.0, 1.0, 3):
            with qp.sweep(h).from_linspace(0.0, 1.0, 3):
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
