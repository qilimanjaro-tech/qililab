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

"""Quantum Machines qprogram integration."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from qililab._optionals import ImportedFeature, OptionalFeature, Symbol, import_optional_dependencies

if TYPE_CHECKING:  # pragma: no cover - typing helper
    from .quantum_machines_compiler import (
        QuantumMachinesCompilationOutput,
        QuantumMachinesCompiler,
    )

__all__ = ["QuantumMachinesCompilationOutput", "QuantumMachinesCompiler"]

QuantumMachinesCompiler = None  # type: ignore[assignment]
QuantumMachinesCompilationOutput = None  # type: ignore[assignment]

_OPTIONAL_FEATURES: list[OptionalFeature] = [
    OptionalFeature(
        name="quantum-machines",
        dependencies=["qm-qua"],
        symbols=[
            Symbol(
                path="qililab.extra.quantum_machines.qprogram.quantum_machines_compiler",
                name="QuantumMachinesCompiler",
                kind="class",
            ),
            Symbol(
                path="qililab.extra.quantum_machines.qprogram.quantum_machines_compiler",
                name="QuantumMachinesCompilationOutput",
                kind="class",
            ),
        ],
    ),
]

_current_module = sys.modules[__name__]

for feature in _OPTIONAL_FEATURES:
    imported_feature: ImportedFeature = import_optional_dependencies(feature)
    for symbol_name, symbol_obj in imported_feature.symbols.items():
        setattr(_current_module, symbol_name, symbol_obj)
