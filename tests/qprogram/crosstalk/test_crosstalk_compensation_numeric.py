"""Numeric checks for QProgram.with_crosstalk_qblox (linear path).

Each case compares the compensated program with ``flux_to_bias`` of the original program at every checkpoint (see
``tests/qprogram/crosstalk/crosstalk_simulation.py``), so it checks the values the hardware gets, not only the structure.
"""

import numpy as np
import pytest

from qililab.core.variables import Domain
from qililab.qprogram import QProgram
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
from qililab.qprogram.qblox_compiler import QbloxCompiler
from qililab.waveforms import Square
from tests.qprogram.crosstalk.crosstalk_simulation import assert_compensated

BUSES = ["flux1", "flux2"]
COUPLED = [[1, 0.5], [0.5, 1]]
OFFSETS = {"flux1": 0.1, "flux2": 0.2}


def make_crosstalk(matrix, flux_offsets=None, buses=None) -> CrosstalkMatrix:
    crosstalk = CrosstalkMatrix.from_array(buses or BUSES, np.array(matrix, dtype=float))
    if flux_offsets:
        crosstalk.flux_offsets = flux_offsets
    return crosstalk


def check(build, crosstalk, quantity="offset"):
    compensated = build().with_crosstalk_qblox(crosstalk)
    assert_compensated(build(), compensated, crosstalk, quantity)
    QbloxCompiler().compile(compensated)


def single_sweep_with_fixed_flux():
    qp = QProgram()
    x = qp.variable("x", Domain.Voltage)
    with qp.for_loop(x, 0, 0.2, 0.1):
        qp.set_offset("flux1", x)
        qp.set_offset("flux2", 0.05)
        qp.wait("flux1", 100)
    return qp


def flux_vs_flux_at_different_levels():
    qp = QProgram()
    x = qp.variable("x", Domain.Voltage)
    y = qp.variable("y", Domain.Voltage)
    with qp.for_loop(x, 0, 0.2, 0.1):
        qp.set_offset("flux1", x)
        with qp.for_loop(y, 0, 0.2, 0.1):
            qp.set_offset("flux2", y)
            qp.wait("flux1", 100)
    return qp


def flux_vs_flux_in_the_inner_loop():
    qp = QProgram()
    x = qp.variable("x", Domain.Voltage)
    y = qp.variable("y", Domain.Voltage)
    with qp.for_loop(x, 0, 0.2, 0.1):
        with qp.for_loop(y, 0, 0.2, 0.1):
            qp.set_offset("flux1", x)
            qp.set_offset("flux2", y)
            qp.wait("flux1", 100)
    return qp


def fixed_flux_next_to_a_sweep():
    qp = QProgram()
    x = qp.variable("x", Domain.Voltage)
    with qp.for_loop(x, 0, 0.2, 0.1):
        qp.set_offset("flux1", x)
        qp.set_offset("flux2", 0.3)
        qp.wait("flux1", 100)
    return qp


def park_then_sweep_the_same_bus():
    qp = QProgram()
    x = qp.variable("x", Domain.Voltage)
    qp.set_offset("flux1", 0.2)
    qp.wait("flux1", 100)
    with qp.for_loop(x, 0, 0.2, 0.1):
        qp.set_offset("flux1", x)
        qp.wait("flux1", 100)
    return qp


def fixed_flux_on_another_bus_then_sweep():
    qp = QProgram()
    x = qp.variable("x", Domain.Voltage)
    qp.set_offset("flux2", 0.05)
    with qp.for_loop(x, 0, 0.2, 0.1):
        qp.set_offset("flux1", x)
        qp.wait("flux1", 100)
    return qp


def reset_after_a_sweep():
    qp = QProgram()
    x = qp.variable("x", Domain.Voltage)
    with qp.for_loop(x, 0, 0.2, 0.1):
        qp.set_offset("flux1", x)
        qp.wait("flux1", 100)
    qp.set_offset("flux1", 0.0)
    qp.wait("flux1", 100)
    return qp


def inner_loop_sweeps_the_same_bus_again():
    qp = QProgram()
    x = qp.variable("x", Domain.Voltage)
    y = qp.variable("y", Domain.Voltage)
    with qp.for_loop(x, 0, 0.2, 0.1):
        qp.set_offset("flux1", x)
        with qp.for_loop(y, 0, 0.2, 0.1):
            qp.set_offset("flux1", y)
            qp.wait("flux1", 100)
    return qp


def park_then_nested_sweep():
    qp = QProgram()
    x = qp.variable("x", Domain.Voltage)
    y = qp.variable("y", Domain.Voltage)
    qp.set_offset("flux1", 0.2)
    with qp.for_loop(x, 0, 0.2, 0.1):
        qp.set_offset("flux2", x)
        with qp.for_loop(y, 0, 0.2, 0.1):
            qp.set_offset("flux1", y)
            qp.wait("flux1", 100)
    return qp


@pytest.mark.parametrize(
    "build",
    [
        single_sweep_with_fixed_flux,
        flux_vs_flux_at_different_levels,
        flux_vs_flux_in_the_inner_loop,
        fixed_flux_next_to_a_sweep,
        park_then_sweep_the_same_bus,
        fixed_flux_on_another_bus_then_sweep,
        reset_after_a_sweep,
        inner_loop_sweeps_the_same_bus_again,
        park_then_nested_sweep,
    ],
)
@pytest.mark.parametrize(
    "matrix, flux_offsets",
    [
        (np.eye(2), None),
        (np.eye(2), OFFSETS),
        ([[1, 0], [0, 2]], OFFSETS),
        ([[1, 0.2], [0, 1]], None),
        (COUPLED, None),
        (COUPLED, OFFSETS),
        (np.linalg.inv([[1, 0.001], [0.001, 1]]), OFFSETS),
    ],
    ids=[
        "identity",
        "identity-offsets",
        "diagonal-offsets",
        "triangular",
        "coupled",
        "coupled-offsets",
        "near-diagonal",
    ],
)
def test_offsets_match_flux_to_bias(build, matrix, flux_offsets):
    check(build, make_crosstalk(matrix, flux_offsets))


@pytest.mark.parametrize("quantity", ["offset", "gain"])
def test_gain_before_a_sweep_is_kept_apart_from_the_offsets(quantity):
    def build():
        qp = QProgram()
        x = qp.variable("x", Domain.Voltage)
        qp.set_gain("flux1", 0.5)
        with qp.for_loop(x, 0, 0.2, 0.1):
            qp.set_offset("flux1", x)
            qp.play("flux1", Square(-0.2, 100))
            qp.wait("flux1", 50)
        return qp

    check(build, make_crosstalk(np.eye(2)), quantity)


def test_constant_folded_into_a_shifted_loop_compiles_with_the_same_iteration_count():
    """Two loop terms plus a constant can't be one VariableExpression, so the constant moves into a shifted copy of
    the innermost compensated loop. The copy must run as many iterations as the loop it shadows."""
    crosstalk = make_crosstalk(COUPLED, OFFSETS)
    compensated = flux_vs_flux_at_different_levels().with_crosstalk_qblox(crosstalk)
    inner = compensated.body.elements[0].elements[-1]

    counts = {QbloxCompiler._calculate_iterations(loop.start, loop.stop, loop.step) for loop in inner.loops}
    assert counts == {3}
    assert len(inner.loops) > 2
    QbloxCompiler().compile(compensated)


def test_single_iteration_loop_raises_a_clear_error():
    qp = QProgram()
    x = qp.variable("x", Domain.Voltage)
    with qp.for_loop(x, 0.2, 0.25, 0.051):
        qp.set_offset("flux1", x)
        qp.wait("flux1", 100)
    with pytest.raises(NotImplementedError, match="Single point loops"):
        qp.with_crosstalk_qblox(make_crosstalk(COUPLED))


def test_inner_loop_setting_only_some_of_the_buses_an_outer_loop_sweeps_raises():
    qp = QProgram()
    x = qp.variable("x", Domain.Voltage)
    y = qp.variable("y", Domain.Voltage)
    with qp.for_loop(x, 0, 0.2, 0.1):
        qp.set_offset("flux1", x)
        qp.set_offset("flux2", x)
        qp.wait("flux2", 75)
        with qp.for_loop(y, 0, 0.2, 0.1):
            qp.set_offset("flux2", y)
            qp.wait("flux2", 50)
    with pytest.raises(NotImplementedError, match="only some of the buses an outer loop sweeps"):
        qp.with_crosstalk_qblox(make_crosstalk(np.eye(2)))


def test_three_loops_on_one_bus_raise_a_clear_error():
    buses = ["flux1", "flux2", "flux3"]
    qp = QProgram()
    x = qp.variable("x", Domain.Voltage)
    y = qp.variable("y", Domain.Voltage)
    z = qp.variable("z", Domain.Voltage)
    with qp.for_loop(x, 0, 0.2, 0.1):
        qp.set_offset("flux1", x)
        with qp.for_loop(y, 0, 0.2, 0.1):
            qp.set_offset("flux2", y)
            with qp.for_loop(z, 0, 0.2, 0.1):
                qp.set_offset("flux3", z)
                qp.wait("flux1", 100)
    dense = [[1, 0.2, 0.05], [0.1, 1, 0.15], [0.03, 0.12, 1]]
    with pytest.raises(NotImplementedError, match="at most two loops"):
        qp.with_crosstalk_qblox(make_crosstalk(dense, buses=buses))
