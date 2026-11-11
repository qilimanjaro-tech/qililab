import numpy as np
import pytest
from qprogram import Range
from qprogram.blocks import Sweep

from qililab.qprogram import QProgram
from qililab.qprogram.blocks import ForLoop
from qililab.qprogram.crosstalk.crosstalk_matrix import CrosstalkMatrix
from tests.qprogram.crosstalk.crosstalk_simulation import (
    assert_compensated,
    compensation_mismatches,
    loop_values,
    simulate,
)

BUSES = ["flux1", "flux2"]


def make_crosstalk(matrix, flux_offsets=None) -> CrosstalkMatrix:
    crosstalk = CrosstalkMatrix.from_array(BUSES, np.array(matrix, dtype=float))
    if flux_offsets:
        crosstalk.flux_offsets = flux_offsets
    return crosstalk


def single_sweep() -> QProgram:
    qp = QProgram()
    x = qp.variable("x")
    with qp.sweep(x).from_range(0, 0.2, 0.1):
        qp.set_offset("flux1", x)
        qp.set_offset("flux2", 0.05)
        qp.wait("flux1", 100)
    return qp


def test_loop_values_match_compiler_count():
    x = QProgram().variable("x")
    assert np.allclose(loop_values(Sweep(x, ForLoop(x, 0, 0.25, 0.1).to_range())), [0.0, 0.125, 0.25])
    assert np.allclose(loop_values(Sweep(x, ForLoop(x, 0.2, 0.2, 0.1).to_range())), [0.2])


def test_simulate_records_state_at_each_wait_and_later_offsets_replace_earlier_ones():
    qp = QProgram()
    x = qp.variable("x")
    qp.set_offset("flux1", 0.3)
    qp.wait("flux1", 100)
    with qp.sweep(x).from_range(0, 0.1, 0.1):
        qp.set_offset("flux1", x)
        qp.wait("flux1", 100)

    snapshots = simulate(qp, BUSES)

    assert [s["offset"]["flux1"] for s in snapshots] == pytest.approx([0.3, 0.0, 0.1])
    assert all(s["offset"]["flux2"] is None for s in snapshots)


def test_identity_without_offsets_accepts_the_original_program():
    assert compensation_mismatches(single_sweep(), single_sweep(), make_crosstalk(np.eye(2))) == []


def test_coupled_matrix_rejects_the_uncompensated_program():
    crosstalk = make_crosstalk([[1, 0.5], [0.5, 1]], {"flux1": 0.1, "flux2": 0.2})
    assert compensation_mismatches(single_sweep(), single_sweep(), crosstalk)


def test_single_sweep_is_compensated():
    crosstalk = make_crosstalk([[1, 0.5], [0.5, 1]], {"flux1": 0.1, "flux2": 0.2})
    assert_compensated(single_sweep(), single_sweep().with_crosstalk_qblox(crosstalk), crosstalk)


def test_parallel_loops_of_different_lengths_raise():
    qp = QProgram()
    x = qp.variable("x")
    y = qp.variable("y")
    with qp.sweep(x).from_range(0, 0.1, 0.05) | qp.sweep(y).from_range(0, 0.1, 0.05) as parallel:
        qp.set_offset("flux1", x)
        qp.wait("flux1", 100)
    # A Parallel refuses loops of different lengths when built, so give it one afterwards.
    parallel.loops[1] = Sweep(y, Range(0, 0.1, 0.025))
    with pytest.raises(ValueError, match="different lengths"):
        simulate(qp, BUSES)
