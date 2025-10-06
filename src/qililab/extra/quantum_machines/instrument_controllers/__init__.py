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
