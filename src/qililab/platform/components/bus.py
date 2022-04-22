from dataclasses import dataclass

from qililab.settings.platform.components.bus import BusSettings


@dataclass
class Bus:
    """Bus class. Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end/beginning of the bus there should be a resonator object, which
    is connected to one or multiple qubits.

    Args:
        settings (BusSettings): Bus settings.
    """

    settings: BusSettings

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over bus elements."""
        return self.settings.__iter__()
