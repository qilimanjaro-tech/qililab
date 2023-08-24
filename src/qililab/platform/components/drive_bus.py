"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces.attenuator import Attenuator
from qililab.drivers.interfaces.awg import AWG
from qililab.drivers.interfaces.local_oscillator import LocalOscillator
from qililab.platform.components.bus_driver import BusDriver
from qililab.platform.components.bus_factory import BusFactory


@BusFactory.register
class DriveBus(BusDriver):
    """Qililab's driver for Drive Bus"""

    def __init__(
        self, alias: str, port: int, awg: AWG, local_oscillator: LocalOscillator | None, attenuator: Attenuator | None
    ):
        """Initialise the bus.

        Args:
            alias: Bus alias
            port (int): Port to target
            awg (AWG): Sequencer
            local_oscillator (LocalOscillator | None): Local oscillator
            attenuator (Attenuator | None): Attenuator
        """
        super().__init__(alias=alias, port=port, awg=awg)
        if local_oscillator:
            self.instruments["local_oscillator"] = local_oscillator
        if attenuator:
            self.instruments["attenuator"] = attenuator

    def to_dict(self, instruments):
        """Generates a dict representation given the Buses and the instruments get_parms()"""
        raise NotImplementedError

    @classmethod
    def from_dict(cls, dictionary: dict) -> "DriveBus":
        """Generates the DriveBus class and passes the instrument params info to be set with set_params(), given a dictionary"""
        _ = dict
        raise NotImplementedError
