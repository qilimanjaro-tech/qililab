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

"""This module contains the QProgram class and all the needed information to build a QProgram.

.. currentmodule:: qililab

QProgram Class
~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~QProgram

Compilers
~~~~~~~~~

.. autosummary::
    :toctree: api

    ~QbloxCompiler
    ~QuantumMachinesCompiler

Other QProgram related Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~Calibration
    ~Domain

"""

import sys

from qililab._optionals import ImportedFeature, OptionalFeature, Symbol, import_optional_dependencies

from .calibration import Calibration
from .crosstalk_matrix import CrosstalkMatrix, FluxVector
from .experiment import Experiment
from .qblox_compiler import QbloxCompilationOutput, QbloxCompiler
from .qprogram import QProgram
from .variable import Domain

__all__ = [
    "Calibration",
    "CrosstalkMatrix",
    "Domain",
    "Experiment",
    "FluxVector",
    "QProgram",
    "QbloxCompilationOutput",
    "QbloxCompiler",
]

__all__ = []

OPTIONAL_FEATURES: list[OptionalFeature] = [
    OptionalFeature(
        name="quantum-machines",
        dependencies=["qm-qua", "qualang-tools"],
        symbols=[
            Symbol(path="qililab.qprogram.quantum_machines_compiler", name="QuantumMachinesCompiler", kind="class"),
            Symbol(path="qililab.qprogram.quantum_machines_compiler", name="QuantumMachinesCompilationOutput", kind="class"),
        ],
    )
]

current_module = sys.modules[__name__]

# Dynamically import (or stub) each feature's symbols and attach them
for feature in OPTIONAL_FEATURES:
    imported_feature: ImportedFeature = import_optional_dependencies(feature)
    for symbol_name, symbol_obj in imported_feature.symbols.items():
        setattr(current_module, symbol_name, symbol_obj)
        __all__ += [symbol_name]
