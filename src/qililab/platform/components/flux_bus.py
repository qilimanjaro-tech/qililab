"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces import AWG, CurrentSource, VoltageSource
from qililab.platform.components.bus_driver import BusDriver
from qililab.platform.components.bus_factory import BusFactory


@BusFactory.register
class FluxBus(BusDriver):
    """Qililab's driver for Flux Bus

    Args:
        alias: Bus alias.
        port (int): Port to target.
        awg (AWG): Sequencer.
        source (CurrentSource | VoltageSource): Bus source instrument.
        distortions (list): Distortions to apply in this Bus.

    Returns:
        BusDriver: BusDriver instance of type flux bus.
    """

    def __init__(
        self, alias: str, port: int, awg: AWG | None, source: CurrentSource | VoltageSource | None, distortions: list
    ):
        """Initialise the bus."""
        super().__init__(alias=alias, port=port, awg=awg, distortions=distortions)
        self.instruments["source"] = source
