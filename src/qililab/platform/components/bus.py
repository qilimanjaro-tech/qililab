"""Bus class."""
from dataclasses import dataclass
from typing import List

from qililab.constants import YAML
from qililab.instruments import (
    Attenuator,
    Instruments,
    MixerBasedSystemControl,
    SystemControl,
)
from qililab.settings import Settings
from qililab.typings import BusSubcategory, Category


class Bus:
    """Bus class. Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end of the bus there should be a qubit or a resonator object,
    which is connected to one or multiple qubits.

    Args:
        settings (BusSettings): Bus settings.
    """

    @dataclass
    class BusSettings(Settings):
        """Bus settings.

        Args:
            subcategory (BusSubcategory): Bus subcategory. Options are "readout" and "control".
            system_control (SystemControl): System control used to control and readout the qubits of the bus.
            target (BusTarget): Bus target (qubit, resonator, coupler).
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
                if isinstance(value, SystemControl | Attenuator | dict):
                    yield name, value

    settings: BusSettings

    def __init__(self, settings: dict, instruments: Instruments):
        self.settings = self.BusSettings(**settings)
        self._replace_settings_dicts_with_instrument_objects(instruments=instruments)

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
    def qubit_ids(self) -> List[int]:
        """Bus 'qubit_ids' property.

        Returns:
            List[int]: IDs of the qubit connected to the bus.
        """
        return [0]  # TODO: Obtain from ChipPlaceHolder

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
            if isinstance(value, dict):
                id_ = value.get(YAML.ID)
                if not isinstance(id_, int):
                    raise ValueError("Invalid value for id.")
                instrument_object = instruments.get(id_=id_, category=Category(name))
                setattr(self.settings, name, instrument_object)

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
