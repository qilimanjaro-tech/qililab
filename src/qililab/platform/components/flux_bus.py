"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces import AWG, CurrentSource, VoltageSource
from qililab.platform.components.bus_factory import BusFactory
from qililab.platform.components.interfaces import BusInterface


@BusFactory.register
class FluxBus(BusInterface):
    """Qililab's driver for Flux Bus"""

    def __init__(self, qubit: int, awg: AWG, source: CurrentSource | VoltageSource):
        """Initialise the bus.

        Args:
            awg (AWG): Bus awg instrument
            source (CurrentSource | VoltageSource): Bus source instrument
        """
        super().__init__(qubit=qubit, awg=awg)
        self.instruments["source"] = source

    def __str__(self):
        """String representation of a FluxBus."""
        return "FluxBus"

    def __eq__(self, other: object) -> bool:
        """compare two FluxBus objects"""
        return str(self) == str(other) if isinstance(other, FluxBus) else False
