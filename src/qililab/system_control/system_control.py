"""SystemControl class."""
from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass
from typing import List

from qililab.constants import RUNCARD
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.platform.components.bus_element import BusElement
from qililab.settings import DDBBElement
from qililab.typings.enums import Parameter, SystemControlName


class SystemControl(BusElement, ABC):
    """SystemControl class."""

    name: SystemControlName

    @dataclass(kw_only=True)
    class SystemControlSettings(DDBBElement):
        """SystemControlSettings class."""

        instruments: List[Instrument]
        all_instruments: InitVar[Instruments]

        def __post_init__(self, all_instruments: Instruments):  # pylint: disable=arguments-differ
            # Cast each instrument dictionary to its corresponding class
            instruments = []
            for inst in self.instruments:
                if isinstance(inst, dict):
                    inst_object = all_instruments.get_instrument(
                        getattr(inst, RUNCARD.ALIAS, None), inst[RUNCARD.CATEGORY], inst[RUNCARD.ID]
                    )
                    instruments.append(inst_object(**inst))
                else:
                    instruments.append(inst)
            self.instruments = instruments
            super().__post_init__()

    settings: SystemControlSettings

    def __init__(self, settings: dict, instruments: Instruments | None = None):
        self.settings = self.SystemControlSettings(**settings, all_instruments=instruments)

    @property
    def id_(self):
        """SystemControl 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def category(self):
        """SystemControl 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

    @property
    def instruments(self) -> List[Instrument]:
        """Instruments controlled by this system control."""
        return self.settings.instruments

    @abstractmethod
    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """sets a parameter to a specific instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """

    @abstractmethod
    def __str__(self):
        """String representation of a SystemControl class."""

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return iter(self.settings.instruments)

    def to_dict(self):
        """Return a dict representation of a SystemControl class."""
        return {
            RUNCARD.ID: self.id_,
            RUNCARD.NAME: self.name.value,
            RUNCARD.CATEGORY: self.settings.category.value,
            RUNCARD.INSTRUMENTS: [inst.to_dict() for inst in self.instruments],
        }
