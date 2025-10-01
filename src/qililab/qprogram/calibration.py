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
from typing import TYPE_CHECKING, Any

from qililab.qprogram.blocks import Block
from qililab.waveforms import IQWaveform, Waveform
from qililab.yaml import yaml

if TYPE_CHECKING:
    from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix


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
