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

"""OperationNode class"""
from dataclasses import dataclass

from qililab.circuit.nodes.node import Node
from qililab.circuit.operations import Operation


@dataclass
class OperationTiming:
    """Class to store timings of an operation"""

    start: int
    end: int


@dataclass
class OperationNode(Node):
    """Node representing an operation acting on one or more qubits

    Args:
        operation (Operation): The operation that is applied
        Node (tuple[int]): The qubits the operation is applied on
        alias (str | None): An optional alias for easily retrieving the node (default = None)
    """

    operation: Operation
    qubits: tuple[int, ...]
    alias: str | None = None
    timing: OperationTiming | None = None
