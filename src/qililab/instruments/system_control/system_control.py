"""SystemControl class."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type, get_type_hints

from qililab.constants import RUNCARD
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.platform.components import BusElement
from qililab.settings import DDBBElement
from qililab.typings import SystemControlCategory, SystemControlSubCategory
from qililab.typings.enums import Category, Parameter


class SystemControl(BusElement, ABC):
    """SystemControl class."""

    @dataclass
    class SystemControlSettings(DDBBElement):
        """SystemControlSettings class."""

        system_control_category: SystemControlCategory
        system_control_subcategory: SystemControlSubCategory

        def __iter__(self):
            """Iterate over Bus elements.

            Yields:
                Tuple[str, ]: a tuple of the instrument category and its alias
            """
            yield from self.__dict__.items()

    settings: SystemControlSettings

    def __init__(self, settings: dict, instruments: Instruments | None = None):
        settings_class: Type[self.SystemControlSettings] = get_type_hints(self).get("settings")  # type: ignore
        self.settings = settings_class(**settings)
        if instruments is not None:
            self._replace_settings_dicts_with_instrument_objects(instruments=instruments)

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
    def system_control_category(self):
        """SystemControl 'system_control_category' property.

        Returns:
            str: settings.system_control_category.
        """
        return self.settings.system_control_category

    @property
    def system_control_subcategory(self):
        """SystemControl 'subcategory' property.

        Returns:
            str: settings.system_control_subcategory.
        """
        return self.settings.system_control_subcategory

    @property
    def supported_instrument_categories(self):
        """get supported instrument categories"""
        return self._get_supported_instrument_categories()

    @abstractmethod
    def _get_supported_instrument_categories(self) -> list[Category]:
        """get supported instrument categories"""

    @abstractmethod
    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """sets a parameter to a specific instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """

    def _replace_settings_dicts_with_instrument_objects(self, instruments: Instruments):
        """Replace dictionaries from settings into its respective instrument classes."""
        for name, value in self.settings:
            if isinstance(value, str):
                instrument_object = instruments.get_instrument(alias=value)
                self._check_for_a_valid_instrument(instrument=instrument_object)
                setattr(self.settings, name, instrument_object)

    def _check_for_a_valid_instrument(self, instrument: Instrument):
        """check if the built instrument is a valid one for this specific SystemControl

        Args:
            instrument (Instrument): Instrument to check

        Raises:
            ValueError: when the instrument is not valid
        """
        if instrument.category not in self.supported_instrument_categories:
            supported_list_values = ",".join([item.value for item in self.supported_instrument_categories])
            raise ValueError(
                "Not supported instrument category for this system control. "
                + f"supported categories are: {supported_list_values} and "
                + f"the category given is: {instrument.category.value}"
            )

    @abstractmethod
    def __str__(self):
        """String representation of a SystemControl class."""

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.settings.__iter__()

    def to_dict(self):
        """Return a dict representation of a SystemControl class."""
        return {
            RUNCARD.ID: self.id_,
            RUNCARD.CATEGORY: self.settings.category.value,
            RUNCARD.SYSTEM_CONTROL_CATEGORY: self.settings.system_control_category.value,
            RUNCARD.SYSTEM_CONTROL_SUBCATEGORY: self.settings.system_control_subcategory.value,
        } | {key: value.alias for key, value in self}
