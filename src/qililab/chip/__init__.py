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
The chip class contains information about the chip and its conections. This information can be reached through the Platform class through a platform object by accessing platform.chip.

Each node in the chip can be a Coil, Coupler, Port, Qubit or Resonator. Each node also has an alias assigned to it. For example, the alias for Qubit nodes is typically ``qubit_n`` where n is the qubit index.

The qubit connectivity (chip topology) can be accessed by calling chip.get_topology(), which returns a networkx graph of the qubits, e.g.

.. code-block:: python

    import networkx as nx
    platform = ql.build_platform(runcard="runcard.yml")
    g = platform.chip.get_topology()
    nx.draw(g, with_labels=True)


.. image:: chip_images/chip_topo.png
   :scale: 60 %
   :alt: alternate text
   :align: center

.. currentmodule:: qililab.chip

Chip Class
~~~~~~~~~~


.. autosummary::
    :toctree: api

    ~Chip

Nodes
~~~~~

.. autosummary::
    :toctree: api

    ~Node
    ~Port
    ~Qubit
    ~Resonator
    ~Coupler
    ~Coil
"""
from .chip import Chip
from .node import Node
from .nodes import Coil, Coupler, Port, Qubit, Resonator
