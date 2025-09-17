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

from abc import ABC, abstractmethod
from typing import Tuple

import networkx as nx
from qibo.models import Circuit


class Placer(ABC):
    """Maps logical qubits to physical qubits."""

    connectivity: nx.Graph

    @abstractmethod
    def __init__(self, connectivity: nx.Graph, *args):
        """Initializes the placer.

        Args:
            connectivity (nx.Graph): Hardware topology.
        """

    @abstractmethod
    def __call__(self, circuit: Circuit):
        """Find initial qubit mapping.

        Method works in-place.

        Args:
            circuit (:class:`qibo.models.circuit.Circuit`): Circuit to be placed.
        """


class Router(ABC):
    """Makes the circuit executable on the given topology."""

    connectivity: nx.Graph

    @abstractmethod
    def __init__(self, connectivity: nx.Graph, *args):
        """Initializes the router.

        Args:
            connectivity (nx.Graph): Hardware topology.
        """

    @abstractmethod
    def __call__(self, circuit: Circuit) -> Tuple[Circuit, dict]:
        """Match circuit to hardware connectivity.

        Args:
            circuit (:class:`qibo.models.circuit.Circuit`): Circuit to be routed.

        Returns:
            (:class:`qibo.models.circuit.Circuit`, dict): Routed circuit and final logical-physical qubit mapping.
        """


class Optimizer(ABC):
    """Reduces the number of gates in the circuit."""

    @abstractmethod
    def __call__(self, circuit: Circuit) -> Circuit:
        """Optimize transpiled circuit.

        Args:
            circuit (:class:`qibo.models.circuit.Circuit`): Circuit to be optimized.

        Returns:
            (:class:`qibo.models.circuit.Circuit`): Optimized circuit.
        """
