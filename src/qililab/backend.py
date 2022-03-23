from typing import Type

from qibo.backends.numpy import NumpyBackend

from qililab import gates
from qililab.circuit import HardwareCircuit
from qililab.config import raise_error


class QililabBackend(NumpyBackend):  # pragma: no cover
    """Hardware backend used to execute circuits on specified lab platforms"""

    def __init__(self) -> None:
        super().__init__()
        self.name = "qililab"
        self.is_hardware = True
        self.platform = None

    def set_platform(self, name: str) -> None:
        """Set platform for controlling quantum devices.

        Args:
            name (str): name of the platform. Options are 'qili'.
        """
        if name == "qili":
            from qililab.platforms.qiliplatform import QiliPlatform as Device
        else:
            raise_error(RuntimeError, f"Platform {name} is not supported.")

        self.platform = Device(name)

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
            raise_error(NotImplementedError, "Hardware backend does not support multi-GPU configuration.")
        if density_matrix:
            raise_error(NotImplementedError, "Hardware backend does not support density matrix simulation.")

        return HardwareCircuit

    def create_gate(self, cls, *args, **kwargs) -> object:
        """Create gate object"""

        return getattr(gates, cls.__name__)(*args, **kwargs)
