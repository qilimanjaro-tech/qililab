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

"""Node class"""
from dataclasses import dataclass

from qililab.settings import Settings
from qililab.typings import FactoryElement


@dataclass(kw_only=True)
class Node(Settings, FactoryElement):
    """This class is used to represent a node of the chip's graph.

    Each node is an element of the chip.

    Args:
        alias (str): Alias of the node
        nodes (list[str]): List of nodes within the node
    """

    alias: str  #: Alias of the node
    nodes: list[str]  #: List of nodes within the node

    def __str__(self):
        """String representation of a node."""
        return f"{self.alias}"
