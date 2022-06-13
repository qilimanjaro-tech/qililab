"""Bus class."""
from typing import Generator, List, Tuple

from qililab.constants import YAML
from qililab.instruments import MixerBasedSystemControl, StepAttenuator, SystemControl
from qililab.platform import BusElement
from qililab.platform.components.targets.target import Target
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
            subcategory (BusSubcategory): Bus subcategory. Options are "readout" and "control".
            system_control (SystemControl): System control used to control and readout the qubits of the bus.
            target (BusTarget): Bus target (qubit, resonator, coupler).
        """

        subcategory: BusSubcategory
        system_control: SystemControl
        target: Target
        attenuator: StepAttenuator | None = None

        def __post_init__(self):
            """Cast each bus element to its corresponding class."""
            for name, value in self:
                if isinstance(value, dict):
                    try:
                        dict_name = value.pop(YAML.NAME)
                    except KeyError:
                        dict_name = value.get(YAML.SUBCATEGORY)
                    elem_obj = Factory.get(dict_name)(value)
                    setattr(self, name, elem_obj)

        def __iter__(
            self,
        ) -> Generator[Tuple[str, BusElement | dict], None, None]:
            """Iterate over Bus elements.

            Yields:
                Tuple[str, ]: _description_
            """
            # TODO: Figure out why dict is in if statement
            for name, value in self.__dict__.items():
                if isinstance(value, BusElement | dict):
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
    def attenuator(self) -> StepAttenuator | None:
        """Bus 'attenuator' property.

        Returns:
            List[int]: settings.attenuator.
        """
        return self.settings.attenuator

    @property
    def qubit_ids(self) -> List[int]:
        """Bus 'qubit_ids' property.

        Returns:
            List[int]: IDs of the qubit connected to the bus.
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
            (QubitControl | QubitReadout | SignalGenerator | Resonator | None): Element class.
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

    def to_dict(self):
        """Return a dict representation of the SchemaSettings class."""
        return {
            YAML.ID: self.id_,
            YAML.CATEGORY: self.settings.category.value,
            YAML.SUBCATEGORY: self.subcategory.value,
        } | {key: value.to_dict() for key, value in self if not isinstance(value, dict)}
