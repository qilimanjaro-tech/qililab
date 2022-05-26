"""Bus class."""
from typing import Generator, List, Tuple

from qililab.constants import YAML
from qililab.instruments import MixerBasedSystemControl, SystemControl
from qililab.platform.components.bus_target.bus_target import BusTarget
from qililab.settings import Settings
from qililab.typings import BusSubcategory, Category
from qililab.utils import Factory, nested_dataclass


class Bus:
    """Bus class. Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end of the bus there should be a qubit or a resonator object,
    which is connected to one or multiple qubits.

    Args:
        settings (BusSettings): Bus settings.
    """

    @nested_dataclass
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

        subcategory: BusSubcategory
        system_control: SystemControl
        target: BusTarget

        def __post_init__(self):
            """Cast each bus element to its corresponding class."""
            for name, value in self:
                if isinstance(value, dict):
                    elem_obj = Factory.get(value.pop(YAML.NAME))(value)
                    setattr(self, name, elem_obj)

        def __iter__(
            self,
        ) -> Generator[Tuple[str, SystemControl | BusTarget], None, None]:
            """Iterate over Bus elements.

            Yields:
                Tuple[str, ]: _description_
            """
            for name, value in self.__dict__.items():
                if isinstance(value, SystemControl | BusTarget | dict):
                    yield name, value

    settings: BusSettings

    def __init__(self, settings: dict):
        self.settings = self.BusSettings(**settings)

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
    def target(self):
        """Bus 'resonator' property.
        Returns:
            Resonator: settings.resonator.
        """
        return self.settings.target

    @property
    def qubit_ids(self) -> List[int]:
        """Bus 'qubit_ids' property.

        Returns:
            List[int]: IDs of the qubit connected to the bus.~
        """
        return self.target.qubit_ids

    @property
    def subcategory(self) -> BusSubcategory:
        """Bus 'subcategory' property.

        Returns:
            BusSubcategory: Subcategory of the bus. Options are "control" or "readout".
        """
        return self.settings.subcategory

    def get_element(self, category: Category, id_: int):
        """Get bus element. Return None if element is not found.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            (QubitControl | QubitReadout | SignalGenerator | Mixer | Resonator | None): Element class.
        """
        if category == Category.QUBIT:
            return self.target.get_qubit(id_=id_)
        return next(
            (element for _, element in self if element.category == category and element.id_ == id_),
            self.system_control.get_element(category=category, id_=id_)
            if isinstance(self.system_control, MixerBasedSystemControl)
            else None,
        )

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.settings.__iter__()
