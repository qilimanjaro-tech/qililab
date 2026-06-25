# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Execute a (new) :class:`qprogram.QProgram` on a qililab platform.

This is the software-domain driver — the spiritual successor to ``ExperimentExecutor`` — adapted to
the unified QProgram AST. Where the legacy stack split orchestration (``Experiment``) from real-time
control (``QProgram``) into two classes, the new QProgram holds both, and the capability validator's
:class:`~qprogram.protocol.ExecutionPlan` tells us each node's domain (``hw`` / ``sw``).

The executor walks the **software region** (forced-``sw`` outer loops + the bus-less orchestration ops
``set_parameter`` / ``get_parameter`` / ``set_crosstalk``), unrolling those loops host-side exactly as
``ExperimentExecutor`` did. At each **hardware frontier** — a maximal fully-hardware subtree — it hands
the subtree to :class:`~qililab.qprogram.v2.qblox_compiler.QbloxCompilerV2`, uploads/runs the resulting
``qpysequence`` on the instruments, and writes the acquired data into the right slice of dense result
tensors (software-loop indices select the outer slice; the hardware-loop sweep fills the interior).

The result is a :class:`qprogram.result.QProgramResult`: one record per measurement carrying one
:class:`~xarray.DataArray` per requested return token — ``iq`` → ``(*sw, *hw, "IQ")``, ``state`` →
``(*sw, *hw)``, ``raw`` → ``(*sw, "time", "IQ")`` — software sweeps outermost.

Scope (this iteration): Qblox hardware; ``ForLoop`` / ``Loop`` / ``Parallel`` software loops; one or more
hardware frontiers; the ``iq`` / ``state`` / ``raw`` return tokens; same-iteration ``get_parameter``
data-flow. QDAC execution and crosstalk lowering are handled elsewhere (platform integration).
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import numpy as np
import xarray as xr
from qprogram.blocks import Average, Block, ForLoop, Loop, Parallel
from qprogram.operations import GetParameter, SetParameter
from qprogram.operations.operation import MeasurementOperation
from qprogram.qprogram import QProgram
from qprogram.result import QProgramResult
from qprogram.variable import Expression
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

from qililab.qprogram.v2.partition import hw_frontier
from qililab.qprogram.v2.qblox_compiler import QbloxCompilerV2
from qililab.qprogram.v2.vendor import SetCrosstalk

if TYPE_CHECKING:
    from collections.abc import Callable

    from qprogram.protocol import ExecutionPlan
    from qprogram.variable import Variable

    from qililab.platform.platform import Platform
    from qililab.qprogram.v2.schema import RuncardBusSchema

#: Software-only operation classes — handled host-side, never compiled to the instrument.
_SW_OPS = (SetParameter, GetParameter, SetCrosstalk)


class _LoopAxis:
    """One swept loop contributing a result-tensor dimension.

    A plain :class:`~qprogram.blocks.ForLoop` / :class:`~qprogram.blocks.Loop` contributes a single
    coordinate; a :class:`~qprogram.blocks.Parallel` contributes one *dimension* whose name is the
    ``"|"``-joined loop-variable ids and which carries one coordinate per co-swept variable (matching
    the reference executor's ``"a|b"`` convention).

    Attributes:
        name: Dimension name — a variable id, or ``"a|b"`` for a parallel axis.
        coords: Mapping ``coordinate-name -> values``; one entry per (co-)swept variable.
        domain: ``"sw"`` (host-driven outer loop) or ``"hw"`` (real-time inner loop).
    """

    __slots__ = ("coords", "domain", "name")

    def __init__(self, name: str, coords: dict[str, np.ndarray], domain: str) -> None:
        self.name = name
        self.coords = coords
        self.domain = domain

    @property
    def size(self) -> int:
        return int(next(iter(self.coords.values())).size)


def _loop_values(block: ForLoop | Loop) -> np.ndarray:
    """Return the sweep values of a loop block as a numpy array (inclusive for ``ForLoop``)."""
    if isinstance(block, ForLoop):
        return block.start + block.step * np.arange(block.num_iterations())
    return np.asarray(block.values)


def _axis_for(block: ForLoop | Loop | Parallel, *, hw: bool) -> _LoopAxis:
    """Build the :class:`_LoopAxis` a loop block contributes (single coord, or co-swept for Parallel)."""
    domain = "hw" if hw else "sw"
    if isinstance(block, Parallel):
        name = "|".join(lp.variable.id for lp in block.loops)
        coords = {lp.variable.id: _loop_values(lp) for lp in block.loops}
        return _LoopAxis(name, coords, domain)
    return _LoopAxis(block.variable.id, {block.variable.id: _loop_values(block)}, domain)


class _MeasurementPlan:
    """Per-measurement tensor metadata + the dense buffers filled during execution.

    One buffer per requested return token (``iq`` / ``state`` allocated up-front; ``raw`` lazily, since
    its ``time`` length is only known once the instrument returns a trace). Software-loop indices select
    the outer slice; the hardware sweep fills the interior.

    Attributes:
        name: Measurement handle name (stable identifier).
        bus: Bus the measurement runs on.
        returns: Requested return tokens.
        sw_axes / hw_axes: Enclosing software / hardware loops (``Average`` excluded), outermost-first.
    """

    def __init__(
        self, name: str, bus: str, returns: tuple[str, ...], sw_axes: list[_LoopAxis], hw_axes: list[_LoopAxis]
    ) -> None:
        self.name = name
        self.bus = bus
        self.returns = returns
        self.sw_axes = sw_axes
        self.hw_axes = hw_axes
        self._sw_shape = tuple(ax.size for ax in sw_axes)
        self._hw_shape = tuple(ax.size for ax in hw_axes)
        self.buffers: dict[str, np.ndarray] = {}
        if "iq" in returns:
            self.buffers["iq"] = np.full((*self._sw_shape, *self._hw_shape, 2), np.nan, dtype=float)
        if "state" in returns:
            self.buffers["state"] = np.full((*self._sw_shape, *self._hw_shape), np.nan, dtype=float)
        self._raw: np.ndarray | None = None  # (*sw, time, 2), allocated on first raw trace

    def ensure_raw(self, time: int) -> np.ndarray:
        """Allocate (once) and return the raw buffer ``(*sw, time, 2)``."""
        if self._raw is None:
            self._raw = np.full((*self._sw_shape, time, 2), np.nan, dtype=float)
        return self._raw

    def _coords_for(self, dims: list[str]) -> dict[str, tuple[str, np.ndarray]]:
        """Coordinates whose owning axis dimension appears in ``dims`` (xarray non-index coords)."""
        out: dict[str, tuple[str, np.ndarray]] = {}
        for ax in self.sw_axes + self.hw_axes:
            if ax.name in dims:
                for coord_name, values in ax.coords.items():
                    out[coord_name] = (ax.name, values)
        return out

    def to_result(self) -> tuple[xr.DataArray | None, dict[str, xr.DataArray]]:
        """Assemble the per-token :class:`~xarray.DataArray`\\ s and the primary array.

        Returns ``(primary, fields)``: ``primary`` is the ``iq`` field when present, else the first
        requested token; ``fields`` maps each available return token to its array.
        """
        sw_names = [ax.name for ax in self.sw_axes]
        hw_names = [ax.name for ax in self.hw_axes]
        fields: dict[str, xr.DataArray] = {}
        if "iq" in self.buffers:
            dims = [*sw_names, *hw_names, "IQ"]
            coords: dict[str, object] = dict(self._coords_for(dims))
            coords["IQ"] = ["I", "Q"]
            fields["iq"] = xr.DataArray(self.buffers["iq"], dims=dims, coords=coords, name=self.name)
        if "state" in self.buffers:
            dims = [*sw_names, *hw_names]
            fields["state"] = xr.DataArray(
                self.buffers["state"], dims=dims, coords=dict(self._coords_for(dims)), name=self.name
            )
        if self._raw is not None:
            dims = [*sw_names, "time", "IQ"]
            coords = dict(self._coords_for(dims))
            coords["time"] = np.arange(self._raw.shape[-2])
            coords["IQ"] = ["I", "Q"]
            fields["raw"] = xr.DataArray(self._raw, dims=dims, coords=coords, name=self.name)
        primary = fields.get("iq")
        if primary is None and fields:
            primary = next(iter(fields.values()))
        return primary, fields


def _collect_measurement_plans(program: QProgram, plan: ExecutionPlan) -> list[_MeasurementPlan]:
    """Pre-walk the AST to compute each measurement's enclosing software/hardware loop axes.

    Mirrors ``ExperimentExecutor._prepare_metadata``: walk the tree carrying the stack of enclosing
    loops, tagging each as software (forced ``sw``) or hardware (``hw``-capable, ``Average`` excluded),
    and record the stack at each measurement leaf. ``Parallel`` contributes one co-swept axis.
    """
    plans: list[_MeasurementPlan] = []
    seen: set[str] = set()

    def hw_capable(node: object) -> bool:
        support = plan.get(node)  # type: ignore[arg-type]
        return bool(support) and "hw" in support

    def walk(block: Block, axes: list[_LoopAxis]) -> None:
        for element in block.elements:
            if isinstance(element, (ForLoop, Loop, Parallel)):
                axis = _axis_for(element, hw=hw_capable(element))
                walk(element, [*axes, axis])
            elif isinstance(element, Average):
                walk(element, axes)  # averaging collapses — contributes no dimension
            elif isinstance(element, Block):
                walk(element, axes)
            elif isinstance(element, MeasurementOperation):
                if element.name in seen:
                    continue
                seen.add(element.name)
                sw_axes = [ax for ax in axes if ax.domain == "sw"]
                hw_axes = [ax for ax in axes if ax.domain == "hw"]
                bus = str(getattr(element, "bus", ""))
                plans.append(_MeasurementPlan(element.name, bus, tuple(element.returns), sw_axes, hw_axes))

    walk(program.body, [])
    return plans


class QProgramExecutor:
    """Drive a new :class:`~qprogram.QProgram` over a qililab :class:`~qililab.platform.Platform`.

    Args:
        platform: The qililab platform (provides instrument access + ``set_parameter`` / ``get_parameter``).
        qprogram: The program to run (already validated + partition-checked).
        plan: The :class:`~qprogram.protocol.ExecutionPlan` from ``validate``.
        bus_schema: The runcard-derived schema bundle (for vendor/channel metadata).
        markers: Per-bus initial marker masks for the Qblox compiler (from the platform).
        ext_trigger: Whether the runcard enables an external trigger (gates ``wait_trigger``).
        qdac_output: QDAC compilation output armed up front by the platform, or ``None``. Coordinated
            with the Qblox run inside :meth:`Platform._run_hw_qblox_v2`.
        debug: Forwarded to the hardware execution path.
    """

    def __init__(
        self,
        platform: Platform,
        qprogram: QProgram,
        plan: ExecutionPlan,
        bus_schema: RuncardBusSchema,
        *,
        markers: dict[str, str] | None = None,
        ext_trigger: bool = False,
        qdac_output: object = None,
        debug: bool = False,
    ) -> None:
        self._platform = platform
        self._qprogram = qprogram
        self._plan = plan
        self._bus_schema = bus_schema
        self._markers = markers
        self._ext_trigger = ext_trigger
        self._qdac_output = qdac_output
        self._crosstalk = None  # qililab CrosstalkMatrix, set by a qililab.set_crosstalk op
        self._debug = debug
        self._plans = _collect_measurement_plans(qprogram, plan)
        self._plan_by_name = {p.name: p for p in self._plans}
        # Maps id(software-loop block) -> current iteration index. Mutated by the loop closures
        # during _execute_operations; the dict's insertion order is the loop nesting (outermost
        # first), so a hardware-frontier closure reads tuple(self._sw_loop_index.values()) as its
        # software-loop multi-index. Mirrors ExperimentExecutor.loop_indices.
        self._sw_loop_index: dict[int, int] = {}

    def execute(self) -> QProgramResult:
        """Run the program and return its :class:`~qprogram.result.QProgramResult`.

        Two-phase, mirroring the legacy ``ExperimentExecutor``: :meth:`_prepare_operations` flattens the
        software region into a flat ``list[Callable]`` of deferred zero-arg closures (software loops
        unrolled at prepare time, each hardware frontier becoming one closure), then
        :meth:`_execute_operations` runs them in order behind a :class:`rich.progress.Progress` bar. The
        result-tensor shapes were pre-computed in :meth:`_collect_measurement_plans` (the metadata pass).
        """
        body = self._qprogram.body
        frontiers = hw_frontier(self._qprogram, self._plan)
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            TimeElapsedColumn(),
        ) as progress:
            if len(frontiers) == 1 and frontiers[0] is body:
                # Pure-hardware program: the whole body compiles as one QProgram (no software loops).
                operations: list[Callable] = [lambda: self._run_frontier(body, sw_index=())]
            else:
                operations = self._prepare_operations(body, progress)
            self._execute_operations(operations, progress)

        result = QProgramResult()
        for mplan in self._plans:
            primary, fields = mplan.to_result()
            if primary is None:  # pragma: no cover - a measurement always has at least one return token
                continue
            result.append_measurement(bus=mplan.bus, name=mplan.name, data=primary, fields=fields)
        return result

    # ------------------------------------------------------------------ software region

    def _hw_capable(self, node: object) -> bool:
        support = self._plan.get(node)  # type: ignore[arg-type]
        return bool(support) and "hw" in support

    def _prepare_operations(self, block: Block, progress: Progress) -> list[Callable]:
        """Flatten a software-region block into a flat list of deferred zero-arg closures.

        Mirrors ``ExperimentExecutor._prepare_operations`` / ``process_elements``: software loops are
        unrolled here (one body copy per iteration), software ops become host-side closures, and each
        hardware frontier becomes one closure that compiles + runs the subtree at the software-loop
        multi-index current when it fires. The closures are executed later by :meth:`_execute_operations`.
        """
        operations: list[Callable] = []
        for element in block.elements:
            if isinstance(element, _SW_OPS):
                operations.append(lambda op=element: self._run_sw_op(op))
            elif isinstance(element, (ForLoop, Loop)) and not self._hw_capable(element):
                operations.extend(self._handle_loop(element, [element.variable], [_loop_values(element)], progress))
            elif isinstance(element, Parallel) and not self._hw_capable(element):
                variables = [lp.variable for lp in element.loops]
                value_arrays = [_loop_values(lp) for lp in element.loops]
                operations.extend(self._handle_loop(element, variables, value_arrays, progress))
            elif isinstance(element, Block) and self._hw_capable(element):
                # A fully-hardware subtree: the frontier. Compile + run it as one QProgram, at the
                # software-loop multi-index that is current when this closure fires (read at run time).
                operations.append(
                    lambda f=element: self._run_frontier(f, sw_index=tuple(self._sw_loop_index.values()))
                )
            elif isinstance(element, Block):
                # A plain software grouping block (no own dimension): splice its closures inline.
                operations.extend(self._prepare_operations(element, progress))
            elif not self._hw_capable(element):
                # A software-dispatched bus op (e.g. a QDAC/flux ``set_offset`` / ``play``) — already
                # programmed by the up-front QDAC compile (self._qdac_output); emits no closure.
                continue
            else:  # pragma: no cover - partition check rejects a bare hardware leaf op here
                msg = f"Unexpected hardware node {type(element).__name__} in software region"
                raise RuntimeError(msg)
        return operations

    def _handle_loop(
        self,
        block: ForLoop | Loop | Parallel,
        variables: list[Variable],
        value_arrays: list[np.ndarray],
        progress: Progress,
    ) -> list[Callable]:
        """Unroll a software loop into closures, with its own nested progress bar.

        Emits (mirroring ``ExperimentExecutor.handle_loop``): a ``create`` closure that adds the loop's
        progress task and registers its index; for each swept point a closure that binds the loop
        variable(s) and advances the loop bar, then the unrolled body closures, then an
        ``advance index`` closure; and finally a ``remove`` closure that drops the task + index.
        """
        operations: list[Callable] = []
        label = ",".join(v.id for v in variables)
        size = min(len(arr) for arr in value_arrays)
        task_ids: dict[int, int] = {}

        def create_progress_bar() -> None:
            task_ids[id(block)] = progress.add_task(f"Looping over {label}", total=size)
            self._sw_loop_index[id(block)] = 0

        def advance_progress_bar(values: tuple[float, ...]) -> None:
            progress.update(
                task_ids[id(block)],
                description=f"Looping over {label}: {values[0] if len(values) == 1 else values}",
            )
            progress.advance(task_ids[id(block)])

        def advance_loop_index() -> None:
            self._sw_loop_index[id(block)] += 1

        def remove_progress_bar() -> None:
            progress.remove_task(task_ids[id(block)])
            del self._sw_loop_index[id(block)]

        operations.append(create_progress_bar)
        for k in range(size):
            current = tuple(float(arr[k]) for arr in value_arrays)

            def bind(vals: tuple[float, ...] = current) -> None:
                for variable, value in zip(variables, vals):
                    variable.set_value(value)

            operations.append(bind)
            operations.append(lambda vals=current: advance_progress_bar(vals))
            operations.extend(self._prepare_operations(block, progress))
            operations.append(advance_loop_index)
        operations.append(remove_progress_bar)
        return operations

    def _execute_operations(self, operations: list[Callable], progress: Progress) -> None:
        """Run the prepared closures in order, advancing the main progress bar (cf. ExperimentExecutor)."""
        main_task = progress.add_task("Executing program", total=len(operations))
        for operation in operations:
            operation()
            progress.advance(main_task)
        progress.update(main_task, description="Executing program (done)")
        progress.refresh()

    def _run_sw_op(self, op: SetParameter | GetParameter | SetCrosstalk) -> None:
        """Execute a software-only orchestration op host-side."""
        from qililab.typings import Parameter

        if isinstance(op, SetParameter):
            # Evaluate against current loop-variable / get_parameter values (same-iteration data-flow).
            value = op.value.evaluate_or_raise() if isinstance(op.value, Expression) else op.value
            self._platform.set_parameter(
                alias=op.alias, parameter=Parameter(op.parameter), value=value, channel_id=op.channel_id
            )
        elif isinstance(op, GetParameter):
            # Thread the read-back value into the destination Variable so later ops in this iteration see it.
            value = self._platform.get_parameter(
                alias=op.alias, parameter=Parameter(op.parameter), channel_id=op.channel_id
            )
            op.variable.set_value(float(value))
        elif isinstance(op, SetCrosstalk):
            # The qililab vendor op carries qililab's own CrosstalkMatrix directly. Record it so the
            # flux-crosstalk compensation (applied to flux ops at compile time — see
            # ``qililab.qprogram.v2.crosstalk``) uses it, and also store it on the platform for the
            # platform's crosstalk helpers (e.g. set_flux_to_zero).
            self._crosstalk = op.crosstalk
            self._platform.set_crosstalk(op.crosstalk)

    # ------------------------------------------------------------------ hardware frontier

    def _run_frontier(self, frontier: Block, sw_index: tuple[int, ...]) -> None:
        """Compile + run a hardware-frontier subtree and store its acquisitions at ``sw_index``."""
        hw_qp = self._wrap_as_qprogram(frontier)
        compiler = QbloxCompilerV2()
        qblox_buses = list(hw_qp.buses)
        single_channel = [
            alias
            for alias in qblox_buses
            if (ref := self._bus_schema.refs.get(alias)) is not None and ref.channel == "single"
        ]
        times_of_flight = self._times_of_flight(qblox_buses)
        output = compiler.compile(
            hw_qp,
            qblox_buses=qblox_buses,
            single_channel=single_channel,
            times_of_flight=times_of_flight,
            markers=self._markers,
            ext_trigger=self._ext_trigger,
        )
        results_by_name = self._platform._run_hw_qblox_v2(
            output, qdac_output=self._qdac_output, debug=self._debug
        )
        for name, qblox_result in results_by_name.items():
            mplan = self._plan_by_name.get(name)
            if mplan is None:  # pragma: no cover - every acquisition should map to a plan
                continue
            self._store_result(mplan, qblox_result, sw_index)

    def _store_result(self, mplan: _MeasurementPlan, qblox_result: object, sw_index: tuple[int, ...]) -> None:
        """Write one acquisition's requested fields into ``mplan``'s buffers at ``sw_index``."""
        if "iq" in mplan.buffers:
            # `.array` is (2, *hw_shape); move I/Q to the trailing axis -> (*hw_shape, 2).
            mplan.buffers["iq"][sw_index] = np.moveaxis(np.asarray(qblox_result.array), 0, -1)
        if "state" in mplan.buffers:
            threshold = getattr(qblox_result, "threshold", None)
            if threshold is not None:
                # `.threshold` is (1, *hw_shape); drop the leading singleton to (*hw_shape).
                mplan.buffers["state"][sw_index] = np.asarray(threshold).reshape(mplan._hw_shape)
        if "raw" in mplan.returns:
            raw = getattr(qblox_result, "raw_measurement_data", None)
            scope = raw.get("scope") if isinstance(raw, dict) else None
            if scope is not None:
                path0 = np.asarray(scope.get("path0", {}).get("data", []))
                path1 = np.asarray(scope.get("path1", {}).get("data", []))
                if path0.size:
                    trace = np.stack([path0, path1], axis=-1)  # (time, 2)
                    mplan.ensure_raw(trace.shape[0])[sw_index] = trace

    def _wrap_as_qprogram(self, frontier: Block) -> QProgram:
        """Build a standalone QProgram whose body is a deep copy of the frontier subtree."""
        hw_qp = QProgram(schema=self._qprogram._schema)
        hw_qp._body = deepcopy(frontier)
        return hw_qp

    def _times_of_flight(self, qblox_buses: list[str]) -> dict[str, int]:
        """Read ``TIME_OF_FLIGHT`` for each ADC bus, mirroring ``Platform.compile_qprogram``."""
        from qililab.typings import Parameter

        tof: dict[str, int] = {}
        for alias in qblox_buses:
            bus = self._platform.buses.get(alias=alias)
            if bus is not None and bus.has_adc():
                tof[alias] = int(bus.get_parameter(Parameter.TIME_OF_FLIGHT))
        return tof


def execute_qprogram_v2(
    platform: Platform,
    qprogram: QProgram,
    plan: ExecutionPlan,
    bus_schema: RuncardBusSchema,
    *,
    debug: bool = False,
) -> QProgramResult:
    """Convenience wrapper constructing a :class:`QProgramExecutor` and running it."""
    return QProgramExecutor(platform, qprogram, plan, bus_schema, debug=debug).execute()


__all__ = ["QProgramExecutor", "execute_qprogram_v2"]
