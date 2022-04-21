from dataclasses import asdict, dataclass, field
from typing import List

from qililab.instruments import Mixer, QubitControl, QubitReadout, SignalGenerator
from qililab.resonator import Resonator
from qililab.typings import dict_factory


@dataclass
class Bus:
    """Bus class"""

    signal_generator: SignalGenerator
    mixer: Mixer
    resonator: Resonator
    qubit_control: None | QubitControl = None
    qubit_readout: None | QubitReadout = None

    def asdict(self):
        """Return all Bus information as a dictionary."""
        result = []
        for attr in asdict(self, dict_factory=dict_factory).values():
            if attr is None:
                continue
            if isinstance(attr, SignalGenerator | QubitReadout | QubitControl | Mixer):
                attr_dict = asdict(attr.settings, dict_factory=dict_factory)
            if isinstance(attr, Resonator):
                attr_dict = attr.asdict()
            result.append(attr_dict)
        return result


@dataclass
class Buses:
    """Buses classes"""

    buses: List[Bus] = field(default_factory=list)

    def append(self, bus: Bus):
        """Append a bus to the list of buses"""
        self.buses.append(bus)

    def asdict(self):
        """Return all Buses information as a dictionary."""
        result = []
        for bus in self.buses:
            result.append(bus.asdict())
        return result
