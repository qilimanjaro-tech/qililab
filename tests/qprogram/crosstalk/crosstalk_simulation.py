"""Numeric check for crosstalk compensation.

Steps through a QProgram the way the hardware would: loops run over the same values the Qblox
compiler uses, and each ``set_offset`` / ``set_gain`` replaces the previous value on its bus. At
every point where time passes (``wait``, ``measure``, ``acquire``, a ``play`` on a bus outside the
crosstalk matrix), it records the offset and gain of each crosstalk bus.

The compensated program is correct when, at every such point, its bias equals
``crosstalk.flux_to_bias`` of the flux that the original program sets at the same point.

Limitations:
    * ``play`` waveforms on crosstalk buses aren't compared. The compensation pass adds plays on
      the other buses, so those plays aren't used as checkpoints either.
    * ``Average`` and ``InfiniteLoop`` bodies run once: repeating them doesn't change the state.
    * A ``Parallel`` whose loops have different lengths raises, instead of guessing how the
      compiler runs it.
"""

from collections.abc import Iterator
from typing import Literal

import numpy as np

from qililab.core.variables import Variable, VariableExpression
from qililab.qprogram.blocks import Block, ForLoop, Loop, Parallel
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
from qililab.qprogram.operations import (
    Acquire,
    AcquireWithCalibratedWeights,
    Measure,
    MeasureReset,
    MeasureResetCalibrated,
    MeasureWithCalibratedWaveform,
    MeasureWithCalibratedWaveformWeights,
    MeasureWithCalibratedWeights,
    Play,
    PlayWithCalibratedWaveform,
    SetGain,
    SetOffset,
    Wait,
    WaitTrigger,
)
from qililab.qprogram.qblox_compiler import QbloxCompiler
from qililab.qprogram.qprogram import QProgram

Quantity = Literal["offset", "gain"]
Snapshot = dict[Quantity, dict[str, float | None]]

_TIME_OPERATIONS = (
    Wait,
    WaitTrigger,
    Acquire,
    AcquireWithCalibratedWeights,
    Measure,
    MeasureWithCalibratedWaveform,
    MeasureWithCalibratedWaveformWeights,
    MeasureWithCalibratedWeights,
    MeasureReset,
    MeasureResetCalibrated,
)
_PLAY_OPERATIONS = (Play, PlayWithCalibratedWaveform)


def loop_values(loop: ForLoop | Loop) -> np.ndarray:
    """Values a loop takes on the hardware, using the Qblox compiler's iteration count."""
    if isinstance(loop, Loop):
        return np.asarray(loop.values, dtype=float)
    iterations = QbloxCompiler._calculate_iterations(loop.start, loop.stop, loop.step)
    if iterations <= 1:
        return np.array([loop.start], dtype=float)[: max(iterations, 0)]
    return np.linspace(loop.start, loop.stop, iterations)


def evaluate(value: float | Variable | VariableExpression | None, env: dict[Variable, float]) -> float | None:
    """Numeric value of an operation argument, given the current loop values."""
    if value is None:
        return None
    if isinstance(value, VariableExpression):
        left = evaluate(value.left, env)
        right = evaluate(value.right, env)
        return left + right if value.operator == "+" else left - right  # type: ignore[operator]
    if isinstance(value, Variable):
        if value not in env:
            raise KeyError(f"Variable {value.label!r} is used outside a loop that defines it.")
        return env[value]
    return float(value)


def simulate(qprogram: QProgram, buses: list[str]) -> list[Snapshot]:
    """Offset and gain of each bus at every point where time passes, in program order.

    A bus that hasn't been set yet is ``None``.
    """
    state: Snapshot = {"offset": dict.fromkeys(buses), "gain": dict.fromkeys(buses)}
    snapshots: list[Snapshot] = []

    def run(block: Block, env: dict[Variable, float]) -> None:
        for element in block.elements:
            if isinstance(element, Block):
                for loop_env in _iterations(element, env):
                    run(element, loop_env)
            elif isinstance(element, SetOffset) and element.bus in buses:
                state["offset"][element.bus] = evaluate(element.offset_path0, env)
            elif isinstance(element, SetGain) and element.bus in buses:
                state["gain"][element.bus] = evaluate(element.gain, env)
            elif isinstance(element, _TIME_OPERATIONS) or (
                isinstance(element, _PLAY_OPERATIONS) and element.bus not in buses
            ):
                snapshots.append({"offset": dict(state["offset"]), "gain": dict(state["gain"])})

    run(qprogram.body, {})
    return snapshots


def _iterations(block: Block, env: dict[Variable, float]) -> Iterator[dict[Variable, float]]:
    if isinstance(block, (ForLoop, Loop)):
        for value in loop_values(block):
            yield {**env, block.variable: float(value)}
    elif isinstance(block, Parallel):
        values = [loop_values(loop) for loop in block.loops]
        if len({len(v) for v in values}) > 1:
            raise ValueError("Parallel loops have different lengths; the simulation doesn't model that case.")
        for point in zip(*values):
            yield {**env, **{loop.variable: float(v) for loop, v in zip(block.loops, point)}}
    else:
        yield env


def compensation_mismatches(
    original: QProgram,
    compensated: QProgram,
    crosstalk: CrosstalkMatrix,
    quantity: Quantity = "offset",
    atol: float = 1e-9,
) -> list[str]:
    """Differences between the compensated program and ``flux_to_bias`` of the original, one line each.

    A checkpoint is compared only once the original program has set ``quantity`` on at least one
    crosstalk bus. Buses the original hasn't set count as flux 0.
    """
    buses = list(crosstalk.matrix.keys())
    reference = simulate(original, buses)
    actual = simulate(compensated, buses)
    if len(reference) != len(actual):
        return [f"different number of checkpoints: original {len(reference)}, compensated {len(actual)}"]

    mismatches = []
    for index, (ref, act) in enumerate(zip(reference, actual)):
        flux = ref[quantity]
        if all(value is None for value in flux.values()):
            continue
        expected = crosstalk.flux_to_bias({bus: 0.0 if value is None else value for bus, value in flux.items()})
        for bus in buses:
            got = act[quantity][bus]
            if got is None or not np.isclose(got, expected[bus], atol=atol):
                mismatches.append(
                    f"checkpoint {index}, {quantity} on {bus}: expected {expected[bus]:.6g}, "
                    f"got {'not set' if got is None else f'{got:.6g}'} (flux {flux})"
                )
    return mismatches


def assert_compensated(
    original: QProgram,
    compensated: QProgram,
    crosstalk: CrosstalkMatrix,
    quantity: Quantity = "offset",
    atol: float = 1e-9,
    max_lines: int = 10,
) -> None:
    """Fail with the first mismatches if the compensated program doesn't match ``flux_to_bias``."""
    mismatches = compensation_mismatches(original, compensated, crosstalk, quantity, atol)
    if mismatches:
        shown = "\n".join(mismatches[:max_lines])
        more = f"\n... and {len(mismatches) - max_lines} more" if len(mismatches) > max_lines else ""
        raise AssertionError(f"{len(mismatches)} mismatches:\n{shown}{more}")
