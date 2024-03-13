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

"""
This module contains all the decomposition and transpilation methods used within qililab.

.. currentmodule:: qililab

Transpilation
~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

Gate Decomposition
~~~~~~~~~~~~~~~~~~

.. currentmodule:: qililab.transpiler

.. autosummary::
    :toctree: api
"""

from .circuit_transpiler import CircuitTranspiler
from .gate_decompositions import GateDecompositions
from .native_gates import Drag, Wait
