from dataclasses import dataclass
from typing import ClassVar, Type

from qibo.backends.numpy import NumpyBackend

from qililab import gates
from qililab.circuit import HardwareCircuit
from qililab.platforms import PLATFORM_BUILDER
from qililab.platforms.platform import Platform


@dataclass
class QililabBackend(NumpyBackend):
    """Hardware backend used to execute circuits on specified lab platforms

    Attributes:
        name (str): Name of the backend.
        is_hardware (bool): Flag used by Qibo to identify a hardware backend.
        platform (object): Platform object describing the lab setup.

    """

    name: str
    is_hardware: bool

    def __init__(self) -> None:
        super().__init__()
        self.platform: Platform
        self.name = "qililab"
        self.is_hardware = True

    def set_platform(self, platform: str) -> None:
        """Set platform for controlling quantum devices.

        Args:
            name (str): Name of the platform.
        """
        self.platform = PLATFORM_BUILDER.build(name=platform)

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
