"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces import AWG, CurrentSource, VoltageSource
from qililab.platform.components.bus_factory import BusFactory
from qililab.platform.components import BusDriver


@BusFactory.register
class FluxBus(BusDriver):
    """Qililab's driver for Flux Bus"""

    def __init__(self, alias: str, qubit: int, awg: AWG, source: CurrentSource | VoltageSource):
        """Initialise the bus.

        Args:
            alias: Bus alias
            awg (AWG): Bus awg instrument
            source (CurrentSource | VoltageSource): Bus source instrument
        """
        super().__init__(alias=alias, qubit=qubit, awg=awg)
        self.instruments["source"] = source

    def __str__(self):
        """String representation of a FluxBus. Prints a drawing of the bus elements."""
        return f"FluxBus {self.alias}: " + "".join(f"--|{instrument}|----" for instrument in self.instruments.values())
