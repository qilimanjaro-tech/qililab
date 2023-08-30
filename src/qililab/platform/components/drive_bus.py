"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces.attenuator import Attenuator
from qililab.drivers.interfaces.awg import AWG
from qililab.drivers.interfaces.local_oscillator import LocalOscillator
from qililab.platform.components.bus_driver import BusDriver
from qililab.platform.components.bus_factory import BusFactory


@BusFactory.register
class DriveBus(BusDriver):
    """Qililab's driver for Drive Bus.

    Args:
        alias: Bus alias.
        port (int): Port to target.
        awg (AWG): Sequencer.
        local_oscillator (LocalOscillator | None): Local oscillator.
        attenuator (Attenuator | None): Attenuator.
        distortions (list): Distortions to apply in this Bus.

    Returns:
        BusDriver: BusDriver instance of type drive bus.
    """

    def __init__(
        self,
        alias: str,
        port: int,
        awg: AWG,
        local_oscillator: LocalOscillator | None,
        attenuator: Attenuator | None,
        distortions: list,
    ):
        """Initialise the bus."""
        super().__init__(alias=alias, port=port, awg=awg, distortions=distortions)
        if local_oscillator:
            self.instruments["local_oscillator"] = local_oscillator
        if attenuator:
            self.instruments["attenuator"] = attenuator
