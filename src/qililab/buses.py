from dataclasses import dataclass, field
from typing import List

from qililab.instruments import QubitControl, QubitReadout, SignalGenerator
from qililab.resonator import Resonator


@dataclass
class Bus:
    """Bus class"""

    resonator: Resonator
    signal_generator: SignalGenerator
    qubit_control: None | QubitControl = None
    qubit_readout: None | QubitReadout = None


@dataclass
class Buses:
    """Buses classes"""

    buses: List[Bus] = field(default_factory=list)

    def append(self, bus: Bus):
        """Append a bus to the list of buses"""
        self.buses.append(bus)
