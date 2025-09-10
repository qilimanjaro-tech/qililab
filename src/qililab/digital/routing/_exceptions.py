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

"""Custom exceptions raised in transpiler routines."""


class BlockingError(Exception):
    """Raise when an error occurs in the blocking procedure"""


class ConnectivityError(Exception):
    """Raise for an error in the connectivity"""


class DecompositionError(Exception):
    """A decomposition error is raised when, during transpiling,
    gates are not correctly decomposed in native gates"""


class PlacementError(Exception):
    """Raise for an error in the initial qubit placement"""


class TranspilerPipelineError(Exception):
    """Raise when an error occurs in the transpiler pipeline"""
