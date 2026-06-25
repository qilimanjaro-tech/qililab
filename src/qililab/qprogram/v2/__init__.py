"""New-QProgram integration layer for qililab.

This package wires the standalone, vendor-agnostic ``qprogram`` package (the *new* QProgram)
into qililab's :class:`~qililab.platform.Platform`. It provides:

- ``capabilities``: build a :class:`qprogram.protocol.PlatformCapabilities` from a runcard.
- ``partition``: the SW-outer / HW-inner structural rule + HW-frontier detection.
- ``executor``: the host-side software-loop driver (the new ``ExperimentExecutor``).
- ``qblox_compiler``: the Qblox compiler adapted to walk the new QProgram AST.

It lives in a ``v2`` namespace alongside the legacy ``qililab.qprogram`` modules during the
migration; the legacy ``QProgram``/``Experiment``/compilers are untouched.

Importing this package activates qililab's own vendor namespace on the core QProgram, so
``program.qililab.set_crosstalk(...)`` works (crosstalk is a qililab-only concern — core ``qprogram``
has no notion of it).
"""

from __future__ import annotations

from qililab.qprogram.v2.vendor import register_qililab_vendor

# Activate the qililab vendor namespace (program.qililab.*) as an import side effect.
register_qililab_vendor()
