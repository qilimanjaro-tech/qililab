from pathlib import Path

from qililab.waveforms import IQPair, Waveform
from qililab.yaml import yaml


@yaml.register_class
class Calibration:
    """A class to manage calibration operations for various buses."""

    def __init__(self) -> None:
        """Initialize a Calibration instance."""
        self.operations: dict[str, dict[str, Waveform | IQPair]] = {}

    def add_operation(self, bus: str, operation: str, waveform: Waveform | IQPair):
        """Add a waveform or IQPair operation to the specified bus.

        Args:
            bus (str): The bus to which the operation will be added.
            operation (str): The name of the operation to add.
            waveform (Waveform | IQPair): The waveform or IQPair instance representing the operation.
        """
        if bus not in self.operations:
            self.operations[bus] = {}
        self.operations[bus][operation] = waveform

    def has_operation(self, bus: str, operation: str) -> bool:
        """Check if there is an associated operation with bus.

        Args:
            bus (str): The bus to check the operation.
            operation (str): The name of the operation to check.

        Returns:
            bool: True, if there is an associated operation with bus. False otherwise.
        """
        if bus not in self.operations or operation not in self.operations[bus]:
            return False
        return True

    def get_operation(self, bus: str, operation: str):
        """Retrieve a specific operation from a bus.

        Args:
            bus (str): The bus from which to retrieve the operation.
            operation (str): The name of the operation to retrieve.

        Raises:
            KeyError: If the specified bus or operation does not exist.

        Returns:
            Waveform | IQPair: The waveform or IQPair associated with the specified operation.
        """
        if bus not in self.operations or operation not in self.operations[bus]:
            raise KeyError("The specified bus or operation does not exist.")
        return self.operations[bus][operation]

    def dump(self, file: str):
        """Dump the current calibration data to a YAML file.

        Args:
            file (str): The file path where the calibration data will be saved. If the file extension
                        is not provided, it defaults to '.yml'.

        Returns:
            str: The path of the saved file.
        """
        path = Path(file) if file.endswith(".yml") or file.endswith(".yaml") else Path(f"{file}.yml")

        with open(file=path, mode="w", encoding="utf-8") as stream:
            yaml.dump(data=self, stream=stream)

        return str(path)

    @classmethod
    def load(cls, file: str):
        """Load calibration data from a YAML file.

        Args:
            file (str): The file path from which to load the calibration data.

        Raises:
            TypeError: If the loaded data is not an instance of the Calibration class.

        Returns:
            Calibration: An instance of the Calibration class with data loaded from the file.
        """
        with open(file=file, mode="r", encoding="utf8") as stream:
            data = yaml.load(stream)
        if not isinstance(data, cls):
            raise TypeError("The loaded data is not an instance of the Calibration class.")
        return data
