from dataclasses import dataclass
from typing import ClassVar, Type, Union

from qibo.backends.numpy import NumpyBackend

from qililab import gates
from qililab.circuit import HardwareCircuit
from qililab.platforms.abstract_platform import AbstractPlatform
from qililab.platforms.qiliplatform import QiliPlatform


@dataclass
class QililabBackend(NumpyBackend):
    """Hardware backend used to execute circuits on specified lab platforms

    Attributes:
        name (str): Name of the backend.
        is_hardware (bool): Flag used by Qibo to identify a hardware backend.
        platform (object): Platform object (child of AbstractPlatform class) describing the lab setup.

    """

    name: ClassVar[str] = "qililab"
    is_hardware: ClassVar[bool] = True

    def __init__(self) -> None:
        super().__init__()
        self.platform: AbstractPlatform

    def set_platform(self, name: str) -> None:
        """Set platform for controlling quantum devices.

        Args:
            name (str): name of the platform. Options are 'qili'.
        """
        if name == "qili":
            self.platform = QiliPlatform(name)
        else:
            raise NotImplementedError(f"Platform {name} is not supported.")

    def get_platform(self) -> str:
        """
        Returns:
            str: Platform name.
        """
        return str(self.platform)

    def circuit_class(self, accelerators: dict = None, density_matrix: bool = False) -> Type[HardwareCircuit]:
        """
        Returns:
            Type[HardwareCircuit]: Circuit class used to create circuit model.
        """
        if accelerators is not None:
            raise NotImplementedError("Hardware backend does not support multi-GPU configuration.")
        if density_matrix:
            raise NotImplementedError("Hardware backend does not support density matrix simulation.")

        return HardwareCircuit

    def create_gate(self, cls, *args, **kwargs) -> object:
        """Create gate object"""

        return getattr(gates, cls.__name__)(*args, **kwargs)
