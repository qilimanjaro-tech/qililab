"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces.attenuator import Attenuator
from qililab.drivers.interfaces.awg import AWG
from qililab.drivers.interfaces.local_oscillator import LocalOscillator
from qililab.platform.components.bus_factory import BusFactory
from qililab.platform.components.interfaces import BusInterface


@BusFactory.register
class DriveBus(BusInterface):
    """Qililab's driver for Drive Bus"""

    def __init__(self, qubit: int, awg: AWG, local_oscillator: LocalOscillator | None, attenuator: Attenuator | None):
        """Initialise the bus.

        Args:
            qubit (int): Qubit
            awg (AWG): Sequencer
            local_oscillator (LocalOscillator | None): Local oscillator
            attenuator (Attenuator | None): Attenuator
        """
        super().__init__(qubit=qubit, awg=awg)
        if local_oscillator:
            self.instruments["local_oscillator"] = local_oscillator
        if attenuator:
            self.instruments["attenuator"] = attenuator

    def __str__(self):
        """String representation of a DriveBus."""
        return "DriveBus"

    def __eq__(self, other: object) -> bool:
        """compare two DriveBus objects"""
        return str(self) == str(other) if isinstance(other, DriveBus) else False
