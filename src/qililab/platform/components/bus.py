from dataclasses import asdict, dataclass
from typing import Dict, List

from qililab.instruments import Mixer, QubitControl, QubitReadout, SignalGenerator
from qililab.platform.components.resonator import Resonator
from qililab.platform.utils.enum_dict_factory import enum_dict_factory


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
