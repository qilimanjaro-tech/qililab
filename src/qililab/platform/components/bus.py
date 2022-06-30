"""Bus class."""
from dataclasses import dataclass
from typing import List

from qililab.chip import Chip, Coupler, Qubit, Resonator
from qililab.constants import BUS, RUNCARD
from qililab.instruments import Attenuator, Instruments, SystemControl
from qililab.settings import DDBBElement
from qililab.typings import BusSubcategory, Category
from qililab.utils import Factory


class Bus:
    """Bus class. Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end of the bus there should be a qubit or a resonator object,
    which is connected to one or multiple qubits.

    Args:
        settings (BusSettings): Bus settings.
    """

    targets: List[Qubit | Resonator | Coupler]  # port target (or targets in case of multiple resonators)

    @dataclass
    class BusSettings(DDBBElement):
        """Bus settings.

        Args:
            subcategory (BusSubcategory): Bus subcategory. Options are "readout" and "control".
            system_control (SystemControl): System control used to control and readout the qubits of the bus.
            port (int): Chip's port where bus is connected.
        """

        subcategory: BusSubcategory
        system_control: SystemControl
        port: int
        attenuator: Attenuator | None = None

        def __iter__(self):
            """Iterate over Bus elements.

            Yields:
                Tuple[str, ]: _description_
            """
            for name, value in self.__dict__.items():
                if name in [Category.SYSTEM_CONTROL.value, Category.ATTENUATOR.value] and value is not None:
                    yield name, value

    settings: BusSettings

    def __init__(self, settings: dict, instruments: Instruments, chip: Chip):
        self.settings = self.BusSettings(**settings)
        self._replace_settings_dicts_with_instrument_objects(instruments=instruments)
        self.targets = chip.get_port_nodes(port_id=self.port)

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
    def port(self):
        """Bus 'resonator' property.
        Returns:
            Resonator: settings.resonator.
        """
        return self.settings.port

    @property
    def attenuator(self) -> Attenuator | None:
        """Bus 'attenuator' property.

        Returns:
            List[int]: settings.attenuator.
        """
        return self.settings.attenuator

    @property
    def subcategory(self) -> BusSubcategory:
        """Bus 'subcategory' property.

        Returns:
            BusSubcategory: Subcategory of the bus. Options are "control" or "readout".
        """
        return self.settings.subcategory

    def _replace_settings_dicts_with_instrument_objects(self, instruments: Instruments):
        """Replace dictionaries from settings into its respective instrument classes."""
        for name, value in self.settings:
            instrument_object = None
            category = Category(name)
            if category == Category.SYSTEM_CONTROL and isinstance(value, dict):
                subcategory = value.get(RUNCARD.SUBCATEGORY)
                if not isinstance(subcategory, str):
                    raise ValueError("Invalid value for subcategory.")
                instrument_object = Factory.get(name=subcategory)(settings=value, instruments=instruments)
            if category == Category.ATTENUATOR and isinstance(value, str):
                instrument_object = instruments.get_instrument(alias=value)
            if instrument_object is None:
                raise ValueError(f"No instrument object found for category {category} and value {value}.")
            setattr(self.settings, name, instrument_object)

    @property
    def target_freqs(self):
        """Bus 'target_freqs' property.

        Returns:
            List[float]: Frequencies of the nodes targetted by the bus.
        """
        return [target.frequency for target in self.targets]

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.settings.__iter__()

    def to_dict(self):
        """Return a dict representation of the SchemaSettings class."""
        return (
            {
                RUNCARD.ID: self.id_,
                RUNCARD.CATEGORY: self.settings.category.value,
                RUNCARD.SUBCATEGORY: self.subcategory.value,
                RUNCARD.SYSTEM_CONTROL: self.system_control.to_dict(),
            }
            | ({RUNCARD.ATTENUATOR: self.attenuator.alias} if self.attenuator is not None else {})
            | {BUS.PORT: self.port}
        )
