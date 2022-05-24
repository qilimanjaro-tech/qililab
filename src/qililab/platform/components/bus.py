"""Bus class."""
from dataclasses import dataclass
from typing import Generator, Optional, Tuple

from qililab.constants import YAML
from qililab.instruments import MixerBasedSystemControl, SystemControl
from qililab.platform.components.qubit import Qubit
from qililab.platform.components.resonator import Resonator
from qililab.settings import Settings
from qililab.typings import BusType, Category
from qililab.utils import Factory


class Bus:
    """Bus class. Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end of the bus there should be a qubit or a resonator object,
    which is connected to one or multiple qubits.

    Args:
        settings (BusSettings): Bus settings.
    """

    @dataclass(kw_only=True)
    class BusSettings(Settings):
        """Bus settings.

        Args:
            qubit_instrument (QubitInstrument): Class containing the instrument used for control/readout of the qubits.
            signal_generator (SignalGenerator): Class containing the signal generator instrument.
            mixer_up (Mixer): Class containing the mixer object used for up-conversion.
            mixer_down (Optional[Mixer]): Class containing the mixer object used for down-conversion.
            resonator (Optional[Resonator]): Class containing the resonator object.
            qubit (Optional[Qubit]): Class containing the qubit object.
        """

        bus_type: BusType
        system_control: SystemControl
        qubit: Optional[Qubit] = None
        resonator: Optional[Resonator] = None

        def __post_init__(self):
            """Cast each bus element to its corresponding class."""
            for name, value in self:
                if isinstance(value, dict):
                    elem_obj = Factory.get(value.pop(YAML.NAME))(value)
                    setattr(self, name, elem_obj)

        def __iter__(
            self,
        ) -> Generator[Tuple[str, SystemControl | Resonator | Qubit | dict], None, None]:
            """Iterate over Bus elements.

            Yields:
                Tuple[str, ]: _description_
            """
            for name, value in self.__dict__.items():
                if isinstance(value, SystemControl | Qubit | Resonator | dict):
                    yield name, value

    settings: BusSettings

    @property
    def id_(self):
        """Bus 'id_' property.
        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def system_control(self):
        """Bus 'system_control' property.
        Returns:
            Resonator: settings.system_control.
        """
        return self.settings.system_control

    @property
    def resonator(self):
        """Bus 'resonator' property.
        Returns:
            Resonator: settings.resonator.
        """
        return self.settings.resonator

    @property
    def qubit(self):
        """Bus 'qubit' property.

        Returns:
            Qubit: settings.qubit.
        """
        return self.settings.qubit

    @property
    def qubit_ids(self) -> list:
        """Bus 'qubit_ids' property.

        Returns:
            List[int]: IDs of the qubit connected to the bus.~
        """
        # FIXME: Cannot use ABC with dataclass
        raise NotImplementedError

    def get_element(self, category: Category, id_: int):
        """Get bus element. Return None if element is not found.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            (QubitControl | QubitReadout | SignalGenerator | Mixer | Resonator | None): Element class.
        """
        return next(
            (element for _, element in self if element.category == category and element.id_ == id_),
            self.system_control.get_element(category=category, id_=id_)
            if isinstance(self.system_control, MixerBasedSystemControl)
            else None,
        )

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.settings.__iter__()
