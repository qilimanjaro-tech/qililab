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

from typing import Any

import numpy as np

from qililab.qprogram.blocks import Block
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
from qililab.waveforms import IQWaveform, Waveform
from qililab.yaml import yaml


@yaml.register_class
class Calibration:
    """A class to manage calibration data."""

    def __init__(self) -> None:
        """Initialize a Calibration instance."""
        self.waveforms: dict[str, dict[str, Waveform | IQWaveform]] = {}
        self.weights: dict[str, dict[str, IQWaveform]] = {}
        self.blocks: dict[str, Block] = {}
        self.crosstalk_matrix: CrosstalkMatrix | None = None
        self.parameters: dict[str, Any] = {}
        self.crosstalk_history: list[dict[str, Any]] = []

    def add_waveform(self, bus: str, name: str, waveform: Waveform | IQWaveform):
        """Add a waveform or IQPair for the specified bus.

        Args:
            bus (str): The bus to which the operation will be added.
            operation (str): The name of the operation to add.
            waveform (Waveform | IQPair): The waveform or IQPair instance representing the operation.
        """
        if bus not in self.waveforms:
            self.waveforms[bus] = {}
        self.waveforms[bus][name] = waveform

    def add_weights(self, bus: str, name: str, weights: IQWaveform):
        """Add a weight for the specified bus.

        Args:
            bus (str): The bus to which the operation will be added.
            operation (str): The name of the operation to add.
            waveform (Waveform | IQPair): The waveform or IQPair instance representing the operation.
        """
        if bus not in self.weights:
            self.weights[bus] = {}
        self.weights[bus][name] = weights

    def add_block(self, name: str, block: Block):
        """Add a block.

        Args:
            name (str): The name of the block to add.
            block (Block): The block to add.
        """
        self.blocks[name] = block

    def has_waveform(self, bus: str, name: str) -> bool:
        """Check if there is an associated waveform for the bus.

        Args:
            bus (str): The bus to check for the waveform.
            operation (str): The name of the waveform to check.

        Returns:
            bool: True if there is an associated waveform with the bus, False otherwise.
        """
        if bus not in self.waveforms or name not in self.waveforms[bus]:
            return False
        return True

    def has_weights(self, bus: str, name: str) -> bool:
        """Check if there are associated weights for the bus.

        Args:
            bus (str): The bus to check for the weights.
            operation (str): The name of the weights to check.

        Returns:
            bool: True if there are associated weights with the bus, False otherwise.
        """
        if bus not in self.weights or name not in self.weights[bus]:
            return False
        return True

    def has_block(self, name: str) -> bool:
        """Check if there is a block with the given name.

        Args:
            name (str): The name of the block to check.

        Returns:
            bool: True if there is a block with the given name, False otherwise.
        """
        return name in self.blocks

    def get_waveform(self, bus: str, name: str):
        """Retrieve waveform for the bus.

        Args:
            bus (str): The bus to check for the waveform.
            name (str): The name of the operation to retrieve.

        Raises:
            KeyError: If the waveform does not exist for the bus.

        Returns:
            Waveform | IQPair: The waveform associated with the bus.
        """
        if bus not in self.waveforms or name not in self.waveforms[bus]:
            raise KeyError(f"The waveform {name} does not exist for the bus {bus}.")
        return self.waveforms[bus][name]

    def get_weights(self, bus: str, name: str):
        """Retrieve weights for the bus.

        Args:
            bus (str): The bus to check for the weights.
            name (str): The name of the weights to retrieve.

        Raises:
            KeyError: If the weights do not exist for the bus.

        Returns:
            IQPair: The weights associated with the bus.
        """
        if bus not in self.weights or name not in self.weights[bus]:
            raise KeyError(f"The weights {name} do not exist for the bus {bus}.")
        return self.weights[bus][name]

    def get_block(self, name: str):
        """Retrieve the block with the given name.

        Args:
            name (str): The name of the block to retrieve.

        Raises:
            KeyError: If the block does not exist.

        Returns:
            Block: The block with the given name.
        """
        if name not in self.blocks:
            raise KeyError(f"The block {name} do not exist.")
        return self.blocks[name]

    def _add_crosstalk_history_iteration(self):
        """Creates a new empty iteration on the crosstalk history tuple."""

        if not self.crosstalk_history:
            iteration_idx = 0
        else:
            iteration_idx = len(self.crosstalk_history)

        self.crosstalk_history.append({})

        self.crosstalk_history[-1]["idx"] = iteration_idx
        self.crosstalk_history[-1]["flux_offsets"] = None
        self.crosstalk_history[-1]["block_diag_matrix"] = None
        self.crosstalk_history[-1]["full_matrix"] = None
        self.crosstalk_history[-1]["previous_matrix"] = self.crosstalk_matrix.matrix
        self.crosstalk_history[-1]["previous_offsets"] = self.crosstalk_matrix.flux_offsets
        self.crosstalk_history[-1]["result_intra"] = None
        self.crosstalk_history[-1]["result_inter"] = None

    def add_intra_crosstalk(
        self,
        flux_offsets: dict[str, float],
        block_diag_xt_matrix: dict[str, dict[str, float]],
    ):
        """Function to save the intra qubit crosstalk results iteration.
        The offsets is stored inside crosstalk_history and crosstalk_matrix.flux_offsets after a transformation.
        The Diagonal matrix is stored raw inside crosstalk_history and crosstalk_matrix.matrix after a transformation.

        The transformations that are used to update crosstalk_matrix.flux_offsets and crosstalk_matrix.matrix are the following:

        .. math:: offset_{new} = M_{diag block} · offset_{old} + offset_{result}

        and

        .. math:: M_{updated} = M_{diag block} · M_{old}

        given the Diagonal Block Matrix and Offset Result as inputs.
        The updated crosstalk matrix will be a diagonal block until the inter-qubit crosstalk is added.

        Args:
            flux_offsets (dict[str, float]): Crosstalk offsets fitted with intra qubit data.
            block_diag_xt_matrix (dict[str, dict[str, float]]): Diagonal crosstalk matrix result from intra qubit fitting.

        Raises:
            ValueError: If no crosstalk has been given to calibration file.
        """
        if not self.crosstalk_matrix:
            raise ValueError("No crosstalk has been given to the Calibration file")

        bus_list = list(self.crosstalk_matrix.matrix.keys())
        if set(bus_list) != set(block_diag_xt_matrix.keys()):
            raise ValueError("Block diagonal crosstalk doesn't contain the same buses as saved crosstalk.")

        self._add_crosstalk_history_iteration()

        self.crosstalk_history[-1]["flux_offsets"] = flux_offsets
        self.crosstalk_history[-1]["block_diag_matrix"] = block_diag_xt_matrix

        diag_crosstalk = CrosstalkMatrix().from_buses(block_diag_xt_matrix)
        old_offsets = np.array([self.crosstalk_matrix.flux_offsets[bus] for bus in bus_list])
        result_offsets = np.array([flux_offsets[bus] for bus in bus_list])

        new_matrix = diag_crosstalk.to_array() @ self.crosstalk_matrix.to_array()
        new_offsets = diag_crosstalk.to_array() @ old_offsets + result_offsets

        self.crosstalk_matrix.matrix = CrosstalkMatrix().from_array(bus_list, new_matrix).matrix
        self.crosstalk_matrix.flux_offsets = dict(zip(bus_list, new_offsets))

        self.crosstalk_history[-1]["result_intra"] = self.crosstalk_matrix.matrix

    def add_inter_crosstalk(self, full_crosstalk_matrix: dict[str, dict[str, float]]):
        r"""Function to save the inter qubit crosstalk results iteration.
        The full crosstalk matrix is stored raw inside crosstalk_history and crosstalk_matrix.matrix after a transformation.

        The transformation used for crosstalk_matrix.matrix is the following:

        .. math:: offset_{new} = \prod_{i=n}^{0} M_{i} · M_{old}

        where n is the number of iterations registered and M_i is the Full Matrix for the given i iteration.
        The resulting crosstalk matrix will be the matrix product of all registered full matrices and the original crosstalk matrix.

        Args:
            full_crosstalk_matrix (dict[str, dict[str, float]]): Full crosstalk matrix result from inter qubit fitting.

        Raises:
            ValueError: If no crosstalk has been given to calibration file.
        """
        if not self.crosstalk_matrix:
            raise ValueError("No crosstalk has been given to the Calibration file")

        bus_list = list(self.crosstalk_matrix.matrix.keys())
        if set(bus_list) != set(full_crosstalk_matrix.keys()):
            raise ValueError("Full crosstalk doesn't contain the same buses as saved crosstalk.")

        self.crosstalk_history[-1]["full_matrix"] = full_crosstalk_matrix

        new_matrix = CrosstalkMatrix().from_buses(self.crosstalk_history[0]["previous_matrix"]).to_array()
        for i in range(len(self.crosstalk_history)):
            full_crosstalk = CrosstalkMatrix().from_buses(self.crosstalk_history[i]["full_matrix"])
            new_matrix = full_crosstalk.to_array()@new_matrix
        
        self.crosstalk_matrix.matrix = CrosstalkMatrix().from_array(bus_list, new_matrix).matrix
        self.crosstalk_history[-1]["result_inter"] = self.crosstalk_matrix.matrix

    def remove_history_step(self, idx: int = -1):
        """Function to remove an iteration inside the crosstalk history in case the user wants to remove a specific faulty calibration.

        Args:
            idx (int, optional): Index number. Defaults to the last value of the list.

        Raises:
            ValueError: If no crosstalk history has been created.
        """
        if not self.crosstalk_history:
            raise ValueError(
                "Crosstalk History is empty. First run `Calibration.add_intra_crosstalk` and `Calibration.add_inter_crosstalk`"
            )

        self.crosstalk_history.pop(idx)
