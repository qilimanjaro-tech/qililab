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

from pathlib import Path

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

    def save_to(self, file: str):
        """Dump the current calibration data to a YAML file.

        Args:
            file (str): The file path where the calibration data will be saved. If the file extension
                        is not provided, it defaults to '.yml'.

        Returns:
            str: The path of the saved file.
        """
        yaml.dump(self, Path(file))

        return file

    @classmethod
    def load_from(cls, file: str):
        """Load calibration data from a YAML file.

        Args:
            file (str): The file path from which to load the calibration data.

        Raises:
            TypeError: If the loaded data is not an instance of the Calibration class.

        Returns:
            Calibration: An instance of the Calibration class with data loaded from the file.
        """
        data = yaml.load(Path(file))
        if not isinstance(data, cls):
            raise TypeError("The loaded data is not an instance of the Calibration class.")

        if isinstance(data.crosstalk_matrix, CrosstalkMatrix):
            if isinstance(data.crosstalk_matrix.matrix, list):
                if not data.crosstalk_matrix.bus_list or len(data.crosstalk_matrix.bus_list) != len(
                    data.crosstalk_matrix.matrix
                ):
                    raise ValueError("Bus list is empty or has the wrong dimensions")
                data.crosstalk_matrix.matrix = CrosstalkMatrix.from_array(
                    buses=data.crosstalk_matrix.bus_list, matrix_array=np.array(data.crosstalk_matrix.matrix)
                )

            if isinstance(data.crosstalk_matrix.flux_offsets, list):
                if not data.crosstalk_matrix.bus_list or len(data.crosstalk_matrix.bus_list) != len(
                    data.crosstalk_matrix.flux_offsets
                ):
                    raise ValueError("Bus list is empty or has the wrong dimensions")
                offset_list = data.crosstalk_matrix.flux_offsets.copy()
                data.crosstalk_matrix.flux_offsets = {}
                for bus, value in zip(data.crosstalk_matrix.bus_list, offset_list):
                    data.crosstalk_matrix.flux_offsets[bus] = value
        return data
