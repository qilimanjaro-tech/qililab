# Copyright 2026 Qilimanjaro Quantum Tech
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
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
from qililab.qprogram.flux_vector import FluxVector
from qililab.qprogram.operations import Play, SetGain, SetOffset


class CrosstalkElements:
    """Supporting class for `QProgram.with_crosstalk_`.
    The elements are classified by type (Play, Offset and Gain) to organize the values of flux vectors,
    location in the block and related buses.

    Args:
        crosstalk (CrosstalkMatrix): Crosstalk to be applied over the elements.
    """

    def __init__(self, crosstalk: CrosstalkMatrix):
        self.crosstalk = crosstalk

        self.element_list: dict[int, tuple[FluxVector, list[int]]] = {}

        self.element_group: dict[str, list[int]] = {}
        self.element: dict[str, list[Play | SetOffset | SetGain]] = {}
        self.flux_vector: dict[str, FluxVector] = {}
        self.flux_vector_bus: dict[str, list[str]] = {}

    def add_element(self, element: Play | SetOffset | SetGain, iteration: int):
        """Adds an element and its iteration inside the block to the dictionary and organizes them in groups.

        Args:
            element (Play | SetOffset | SetGain): Qprogram `play`, `set_offset` or `set_gain` elements.
            iteration (int): location of the element inside the block list.
        """

        operation = str(element.__class__)
        self.element[operation].append(element)
        self.element_group[operation].append(iteration)
        self.flux_vector_bus[operation].append(element.bus)

        for ii in self.element_group[operation]:
            self.element_list[ii] = (self.flux_vector[operation], self.element_group[operation])

    def check_flux_vector(self, element: Play | SetOffset | SetGain):
        """Function to verify the flux vectors of each element and in case they don't exist,
        create empty dictionary entries.

        Args:
            element (Play | SetOffset | SetGain): Qprogram `play`, `set_offset` or `set_gain` elements.
        """
        operation = str(element.__class__)
        if operation not in self.flux_vector_bus.keys() or element.bus in self.flux_vector_bus[operation]:
            self.restart_flux_vector(operation, check_after_loop=True)

    def restart_flux_vector(self, operation: str | None = None, check_after_loop: bool = False):
        """Function create or overwrite empty dictionary entries for each operation given.
        If no operations given it does it for every element in those dictionaries.

        Args:
            operation (str | None, optional): Class of the element to be restarted.
                                                Defaults to None implying restarting all operations in the dictionaries.
            check_after_loop (bool, optional): Trigger to avoid restarting the flux vector after starting a new loop. Defaults to False.
        """

        if operation is not None:
            self.element[operation] = []
            self.element_group[operation] = []
            self.flux_vector_bus[operation] = []
            if operation not in self.flux_vector or not check_after_loop:
                self.flux_vector[operation] = FluxVector()
                self.flux_vector[operation].set_crosstalk(self.crosstalk)
        else:
            for operation in self.element_group.keys():
                self.element[operation] = []
                self.element_group[operation] = []
                self.flux_vector_bus[operation] = []
                if operation not in self.flux_vector or not check_after_loop:
                    self.flux_vector[operation] = FluxVector()
                    self.flux_vector[operation].set_crosstalk(self.crosstalk)


class NonLinearFlagState:
    def __init__(self, offsets_index: int = 0, plays_index: int = 0):
        """Tracks cursor positions and flags during non-linear element processing."""
        self.offsets_index = offsets_index
        self.plays_index = plays_index
        self.last_appended_offset: int = -1
        self.offset_defined: bool = False
        self.wait_defined: bool = False
        self.plays_defined: bool = False
        self.block_defined: bool = False
        self.play_bus_list: list[str] = []

    def on_offset(self):
        """Modify offset flags after set_offset is called."""
        if self.wait_defined or self.plays_defined or self.block_defined:
            self.offsets_index += 1  # A new offset index is used every time the offset is modified
        self.last_appended_offset = self.offsets_index  # This prevents repeating offsets when no time has passed
        self.offset_defined = True  # Flag for on_wait and on_block

    def on_play(self, bus: str):
        """Modify play and offset flags after play is called."""
        self.play_bus_list.append(bus)  # bus explicitly used for play
        self.plays_index += 1  # A new play index is used every time there is a new play for used buses
        self.plays_defined = True  # Flag for on_block (wait is not relevant for a play)
        self.offset_defined = True  # Flag for on_wait and on_block

    def on_wait(self):
        """Modify wait flags after wait is called."""
        if self.offset_defined and not self.wait_defined:
            self.wait_defined = True  # Used to modify the offset index after a wait
            self.last_appended_offset = -1  # Reset last_appended_offset after every wait

    def on_block(self):
        """Modify offset and wait flags after a loo block is created."""
        if self.offset_defined and (self.wait_defined or self.plays_defined or self.block_defined):
            self.block_defined = False  # Every block has its own block state
            self.wait_defined = False  # Every block has its own wait state
            self.offsets_index += 1  # A new block implies a new offset index
            self.last_appended_offset = -1  # Reset last_appended_offset after every loop

    def after_block(self):
        """Modify block defined flag after a block is traversed."""
        self.block_defined = True
        self.last_appended_offset = -1  # Reset last_appended_offset after every loop
