from pathlib import Path

from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
from qililab.waveforms import IQPair, Waveform
from qililab.yaml import yaml


@yaml.register_class
class Calibration:
    """A class to manage calibration data."""

    def __init__(self) -> None:
        """Initialize a Calibration instance."""
        self.waveforms: dict[str, dict[str, Waveform | IQPair]] = {}
        self.weights: dict[str, dict[str, IQPair]] = {}
        self.crosstalk_matrix: CrosstalkMatrix | None = None

    def add_waveform(self, bus: str, name: str, waveform: Waveform | IQPair):
        """Add a waveform or IQPair for the specified bus.

        Args:
            bus (str): The bus to which the operation will be added.
            operation (str): The name of the operation to add.
            waveform (Waveform | IQPair): The waveform or IQPair instance representing the operation.
        """
        if bus not in self.waveforms:
            self.waveforms[bus] = {}
        self.waveforms[bus][name] = waveform

    def add_weights(self, bus: str, name: str, weights: IQPair):
        """Add a weight for the specified bus.

        Args:
            bus (str): The bus to which the operation will be added.
            operation (str): The name of the operation to add.
            waveform (Waveform | IQPair): The waveform or IQPair instance representing the operation.
        """
        if bus not in self.weights:
            self.weights[bus] = {}
        self.weights[bus][name] = weights

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
        return data
