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

"""Qubit class"""
from dataclasses import dataclass

from qililab.chip.node import Node
from qililab.typings import NodeName
from qililab.utils import Factory


@Factory.register
@dataclass
class Qubit(Node):
    """This class is used to represent each of the qubits in a chip.

    Each qubit has a frequency associated to it and an index within the chip.

    Args:
        frequency (float): frequency of the qubit
        qubit_index (int): qubit index
    """

    name = NodeName.QUBIT
    frequency: float  #: frequency of the qubit
    qubit_index: int  #: index of the qubit
