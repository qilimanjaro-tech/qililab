"""Runtime helpers for Quantum Machines optional integration."""

from __future__ import annotations

from typing import Any, Callable, cast

from qililab._optionals import OptionalFeature, Symbol, import_optional_dependencies

_QM_RUNTIME = OptionalFeature(
    name="quantum-machines",
    dependencies=[
        "qm-qua",
        "qualang-tools",
    ],
    symbols=[
        Symbol(path="qm", name="generate_qua_script", kind="callable"),
    ],
)

_runtime_symbols = import_optional_dependencies(_QM_RUNTIME).symbols

# Re-export runtime names (real or stubs)
generate_qua_script: "Callable[..., str]" = cast("Any", _runtime_symbols["generate_qua_script"])

__all__ = ["generate_qua_script"]
