"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces import AWG, CurrentSource, VoltageSource
from qililab.platform.components.bus_driver import BusDriver
from qililab.platform.components.bus_factory import BusFactory


@BusFactory.register
class FluxBus(BusDriver):
    """Qililab's driver for Flux Bus"""

    def __init__(self, alias: str, port: int, awg: AWG | None, source: CurrentSource | VoltageSource | None):
        """Initialise the bus.

        Args:
            alias: Bus alias
            port: Port to target
            awg (AWG): Bus awg instrument
            source (CurrentSource | VoltageSource): Bus source instrument
        """
        super().__init__(alias=alias, port=port, awg=awg)
        self.instruments["source"] = source
