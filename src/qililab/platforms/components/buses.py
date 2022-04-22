from dataclasses import asdict, dataclass, field
from typing import Dict, List

from qililab.instruments import Mixer, QubitControl, QubitReadout, SignalGenerator
from qililab.platforms.components.resonator import Resonator
from qililab.platforms.utils.enum_dict_factory import enum_dict_factory


@dataclass
class Bus:
    """Bus class. Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end/beginning of the bus there should be a resonator object, which
    is connected to one or multiple qubits.

    Args:
        qubit_control (None | QubitControl): Class containing the qubit control instrument.
        qubit_readout (None | QubitReadout): Class containing the qubit readout instrument.
        signal_generator (SignalGenerator): Class containing the signal generator instrument.
        mixer (Mixer): Class containing the mixer object, used for up- or down-conversion.
        resonator (Resonator): Class containing the resonator object.
    """

    signal_generator: SignalGenerator
    mixer: Mixer
    resonator: Resonator
    qubit_control: None | QubitControl = None
    qubit_readout: None | QubitReadout = None

    def asdict(self) -> List[Dict]:
        """Return all Bus information as a dictionary."""
        result = []
        for attr in asdict(self, dict_factory=enum_dict_factory).values():
            if attr is None:
                continue
            if isinstance(attr, SignalGenerator | QubitReadout | QubitControl | Mixer):
                attr_dict = asdict(attr.settings, dict_factory=enum_dict_factory)
            if isinstance(attr, Resonator):
                attr_dict = attr.asdict()
            result.append(attr_dict)
        return result


@dataclass
class Buses:
    """Class used as a container of Bus objects.

    Args:
        buses (List[Bus]): List of Bus objects.
    """

    buses: List[Bus] = field(default_factory=list)

    def append(self, bus: Bus):
        """Append a bus to the list of buses.

        Args:
            bus (Bus): Bus object to append."""
        self.buses.append(bus)

    def asdict(self) -> List[List[Dict]]:
        """Return all Buses information as a dictionary."""
        return [bus.asdict() for bus in self.buses]
