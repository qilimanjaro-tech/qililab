"""Bus class."""
from copy import deepcopy
from dataclasses import dataclass
from typing import List

from qililab.chip import Chip, Coil, Coupler, Qubit, Resonator
from qililab.constants import BUS, RUNCARD
from qililab.instruments.instruments import Instruments
from qililab.settings import DDBBElement
from qililab.system_control import SimulatedSystemControl, SystemControl
from qililab.typings import Category, Node, Parameter
from qililab.utils import Factory


class Bus:
    """Bus class. Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end of the bus there should be a qubit or a resonator object,
    which is connected to one or multiple qubits.

    Args:
        settings (BusSettings): Bus settings.
    """

    targets: List[Qubit | Resonator | Coupler | Coil]  # port target (or targets in case of multiple resonators)

    @dataclass
    class BusSettings(DDBBElement):
        """Bus settings.

        Args:
            bus_category (BusCategory): Bus category.
            bus_subcategory (BusSubCategory): Bus subcategory
            system_control (SystemControl): System control used to control and readout the qubits of the bus.
            port (int): Chip's port where bus is connected.
        """

        system_control: SystemControl
        port: int

        def __iter__(self):
            """Iterate over Bus elements.

            Yields:
                Tuple[str, ]: _description_
            """
            for name, value in self.__dict__.items():
                if name == Category.SYSTEM_CONTROL.value and value is not None:
                    yield name, value

    settings: BusSettings

    def __init__(self, settings: dict, platform_instruments: Instruments, chip: Chip):
        self.settings = self.BusSettings(**settings)
        self._replace_settings_dicts_with_instrument_objects(platform_instruments=platform_instruments)
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
    def category(self):
        """Bus 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

    def _replace_settings_dicts_with_instrument_objects(self, platform_instruments: Instruments):
        """Replace dictionaries from settings into its respective instrument classes."""
        for name, value in deepcopy(self.settings):
            instrument_object = None
            category = Category(name)
            if category == Category.SYSTEM_CONTROL and isinstance(value, dict):
                instrument_object = Factory.get(name=value.pop(RUNCARD.NAME))
                if instrument_object == SimulatedSystemControl:
                    instrument = instrument_object(settings=value)
                else:
                    instrument = instrument_object(settings=value, platform_instruments=platform_instruments)
            if instrument is None:
                raise ValueError(f"No instrument object found for category {category.value} and value {value}.")
            setattr(self.settings, name, instrument)

    def __str__(self):
        """String representation of a bus. Prints a drawing of the bus elements."""
        return f"Bus {self.id_}:  ----{self.system_control}---" + "".join(
            f"--|{target}|----" for target in self.targets
        )

    def __eq__(self, other: object) -> bool:
        """compare two Bus objects"""
        return str(self) == str(other) if isinstance(other, Bus) else False

    @property
    def target_freqs(self):
        """Bus 'target_freqs' property.

        Returns:
            List[float]: Frequencies of the nodes that have frequencies
        """
        return list(
            filter(
                None, [target.frequency if hasattr(target, Node.FREQUENCY.value) else None for target in self.targets]
            )
        )

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.settings.__iter__()

    def to_dict(self):
        """Return a dict representation of the SchemaSettings class."""
        return {
            RUNCARD.ID: self.id_,
            RUNCARD.CATEGORY: self.category.value,
            RUNCARD.SYSTEM_CONTROL: self.system_control.to_dict(),
            BUS.PORT: self.port,
        }

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """_summary_

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        self.system_control.set_parameter(parameter=parameter, value=value, channel_id=channel_id)
