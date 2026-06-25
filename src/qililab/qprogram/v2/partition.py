"""SW-outer / HW-inner structural rule for the new QProgram.

``platform.execute`` only accepts programs that cleanly bipartition into an outer **software**
region (host-driven loops over platform parameters) and inner **hardware** regions (maximal pure-
hardware subtrees compiled to a single instrument execution). This module:

- classifies each node as *hardware-capable* using the :func:`qprogram.validation.validate`
  execution plan (a node is hardware-capable iff ``"hw"`` is in its domain set),
- :func:`hw_frontier` finds the maximal pure-hardware subtree roots (the points where the executor
  hands off to the Qblox compiler), and
- :func:`assert_sw_outer_hw_inner` rejects any program that interleaves the two regions — e.g. a
  software ``set_parameter`` inside a hardware loop, or a bare hardware op placed directly in a
  software loop instead of being wrapped in an inner hardware block.

The rule, given the plan ``hw_capable(node)``:

- A *pure-hardware* block (``hw`` in its domain) and everything inside it is compiled as one
  hardware execution; it must contain no software op and no non-hardware sub-block.
- A *software* block may contain software ops, nested software blocks, and whole pure-hardware
  blocks (the inner programs) — but **not** a bare hardware leaf op, which must be wrapped in an
  inner hardware block (``average()`` / ``for_loop()``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qprogram.blocks import Block
from qprogram.operations.operation import Operation

if TYPE_CHECKING:
    from collections.abc import Mapping

    from qprogram.qprogram import QProgram

    Node = Block | Operation
    Plan = Mapping[Node, frozenset[str]]


class QProgramStructureError(ValueError):
    """Raised when a QProgram does not obey the SW-outer / HW-inner structure."""


def _is_sw_op(node: object) -> bool:
    """Return whether ``node`` is a software-dispatched (bus-less orchestration) operation.

    Identified structurally by an empty ``BUS_ATTRS`` (the op names no bus): the core
    ``set_parameter`` / ``get_parameter`` and qililab's vendor ``set_crosstalk`` are bus-less and
    software-dispatched, while everything else (Play, Measure, Wait, Sync, the ``Set*`` bus ops, and
    every other vendor op) names a bus and is a hardware leaf. The structural marker keeps this
    independent of which package owns each op — crosstalk now lives in the qililab vendor, not core.
    """
    return isinstance(node, Operation) and getattr(type(node), "BUS_ATTRS", ("bus",)) == ()


def _hw_capable(node: Node, plan: Plan) -> bool:
    """Return whether ``node`` can run in real-time hardware, per the execution plan."""
    domains = plan.get(node)
    return bool(domains) and "hw" in domains


def _children(block: Block) -> list[Node]:
    """Return the structural children of ``block``.

    For a :class:`~qprogram.blocks.Conditional` the children are the arm and else bodies (its
    ``elements`` are empty); every other block exposes them via ``elements``.
    """
    arms = getattr(block, "arms", None)
    if arms is not None:  # Conditional: arms is a list of (condition, body) pairs.
        bodies: list[Node] = [body for _condition, body in arms]
        else_body = getattr(block, "else_body", None)
        if else_body is not None:
            bodies.append(else_body)
        return bodies
    return list(block.elements)


def _root_hw_capable(program: QProgram, plan: Plan) -> bool:
    """Hardware-capability of the program body.

    The validator does not always assign a domain to the root body, so fall back to "every child is
    hardware-capable" when it is missing from the plan.
    """
    domains = plan.get(program.body)
    if domains is not None:
        return "hw" in domains
    return all(_hw_capable(child, plan) for child in _children(program.body))


def hw_frontier(program: QProgram, plan: Plan) -> list[Node]:
    """Return the maximal pure-hardware subtree roots — the HW/SW hand-off points.

    Each returned node is hardware-capable while its parent is not, so the executor compiles and
    runs each frontier subtree as one instrument execution. A fully-hardware program yields
    ``[program.body]``.
    """
    if _root_hw_capable(program, plan):
        return [program.body]

    frontier: list[Node] = []

    def descend(block: Block) -> None:
        for child in _children(block):
            if isinstance(child, Block):
                if _hw_capable(child, plan):
                    frontier.append(child)
                else:
                    descend(child)
            elif _hw_capable(child, plan):
                # A bare hardware leaf op in the software region is its own (degenerate) frontier;
                # assert_sw_outer_hw_inner rejects this, but hw_frontier stays total.
                frontier.append(child)

    descend(program.body)
    return frontier


def assert_sw_outer_hw_inner(program: QProgram, plan: Plan) -> None:
    """Validate that ``program`` obeys the SW-outer / HW-inner structure.

    Args:
        program: The (expanded, validated) program to check.
        plan: The execution plan from :func:`qprogram.validation.validate`.

    Raises:
        QProgramStructureError: If a software operation appears inside a hardware region, a
            non-hardware block is nested in a hardware region, or a bare hardware operation is
            placed directly in a software loop instead of an inner hardware block.
    """

    def check(block: Block, region: str) -> None:
        for child in _children(block):
            if region == "hw":
                if _is_sw_op(child):
                    msg = (
                        f"software operation {type(child).__name__} appears inside a hardware "
                        f"region; software operations (set_parameter / get_parameter / "
                        f"set_crosstalk) must live in outer software loops, not inside a hardware "
                        f"block such as average()/for_loop()."
                    )
                    raise QProgramStructureError(msg)
                if isinstance(child, Block):
                    if not _hw_capable(child, plan):
                        msg = (
                            f"block {type(child).__name__} inside a hardware region is not fully "
                            f"hardware (it most likely contains a software operation or an "
                            f"arbitrary-value loop); a hardware region must be entirely hardware."
                        )
                        raise QProgramStructureError(msg)
                    check(child, "hw")
                # hardware leaf ops are fine inside a hardware region
            else:  # region == "sw"
                if _is_sw_op(child):
                    continue  # software op in software region — fine
                if isinstance(child, Block):
                    check(child, "hw" if _hw_capable(child, plan) else "sw")
                elif _hw_capable(child, plan):
                    bus = getattr(child, "bus", None)
                    where = f" on bus {bus!r}" if bus is not None else ""
                    msg = (
                        f"hardware operation {type(child).__name__}{where} is placed directly in a "
                        f"software loop; wrap it in an inner hardware block such as average() or "
                        f"for_loop() so it can be compiled to the instrument. Software operations "
                        f"must be the outer loops and hardware operations the inner ones."
                    )
                    raise QProgramStructureError(msg)
                # else: a software-dispatched leaf op (e.g. a QDAC/flux ``set_offset`` / ``play`` on a
                # software-only bus) — legitimately lives in the software region; the QDAC compiler
                # programs it up front, so nothing more to assert here.

    check(program.body, "hw" if _root_hw_capable(program, plan) else "sw")


__all__ = ["QProgramStructureError", "assert_sw_outer_hw_inner", "hw_frontier"]
