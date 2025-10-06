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

"""Quantum Machines instrument controller integration."""

import sys

from qililab._optionals import ImportedFeature, OptionalFeature, Symbol, import_optional_dependencies

__all__: list[str] = []

_OPTIONAL_FEATURES: list[OptionalFeature] = [
    OptionalFeature(
        name="quantum-machines",
        dependencies=["qm-qua", "qualang-tools"],
        symbols=[
            Symbol(
                path="qililab.extra.quantum_machines.instrument_controllers.quantum_machines_cluster_controller",
                name="QuantumMachinesClusterController",
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
        __all__.append(symbol_name)
