from dataclasses import asdict, dataclass
from typing import Dict, List

from qililab.instruments import Mixer, QubitControl, QubitReadout, SignalGenerator
from qililab.platform.components.resonator import Resonator
from qililab.platform.utils.enum_dict_factory import enum_dict_factory
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

    def to_dict(self) -> List[Dict]:
        """Return all Bus information as a dictionary."""
        result = []
        for attr in asdict(self, dict_factory=enum_dict_factory).values():
            if attr is None:
                continue
            if isinstance(attr, SignalGenerator | QubitReadout | QubitControl | Mixer):
                attr_dict = asdict(attr.settings, dict_factory=enum_dict_factory)
            if isinstance(attr, Resonator):
                attr_dict = attr.to_dict()
            result.append(attr_dict)
        return result

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over bus elements."""
        return self.settings.__iter__()
