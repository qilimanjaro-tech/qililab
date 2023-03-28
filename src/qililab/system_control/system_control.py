"""SystemControl class."""
import contextlib
from abc import ABC
from dataclasses import InitVar, dataclass
from typing import List, Type, get_type_hints

from qililab.constants import RUNCARD
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.instruments import Instruments
from qililab.platform.components.bus_element import BusElement
from qililab.pulse import PulseBusSchedule
from qililab.settings import DDBBElement
from qililab.typings.enums import Parameter, SystemControlName
from qililab.utils import Factory


@Factory.register
class SystemControl(BusElement, ABC):
    """SystemControl class."""

    name = SystemControlName.SYSTEM_CONTROL

    @dataclass(kw_only=True)
    class SystemControlSettings(DDBBElement):
        """SystemControlSettings class."""

        instruments: List[Instrument]
        platform_instruments: InitVar[Instruments]

        def __post_init__(self, platform_instruments: Instruments):  # type: ignore # pylint: disable=arguments-differ
            # ``self.instruments`` contains a list of instrument aliases
            self.instruments = [platform_instruments.get_instrument(alias=i) for i in self.instruments]  # type: ignore
            super().__post_init__()

    settings: SystemControlSettings

    def __init__(self, settings: dict, platform_instruments: Instruments | None = None):
        settings_class: Type[self.SystemControlSettings] = get_type_hints(self).get("settings")  # type: ignore
        self.settings = settings_class(**settings, platform_instruments=platform_instruments)

    def generate_program_and_upload(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int
    ) -> None:
        """Translate a Pulse Bus Schedule to an AWG program and upload it

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration
        """
        for instrument in self.instruments:
            instrument.generate_program_and_upload(
                pulse_bus_schedule=pulse_bus_schedule,
                nshots=nshots,
                repetition_duration=repetition_duration,
            )

    def run(self) -> None:
        """Run the uploaded program"""
        for instrument in self.instruments:
            instrument.run()

    def __str__(self):
        """String representation of a SystemControl class."""
        return "".join(f"-|{instrument}|-" for instrument in self.instruments)

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return iter(self.settings.instruments)

    def to_dict(self):
        """Return a dict representation of a SystemControl class."""
        return {
            RUNCARD.ID: self.id_,
            RUNCARD.NAME: self.name.value,
            RUNCARD.CATEGORY: self.settings.category.value,
            RUNCARD.INSTRUMENTS: [inst.alias for inst in self.instruments],
        }

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

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Sets the parameter of a specific instrument.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        for instrument in self.instruments:
            with contextlib.suppress(ParameterNotFound):
                instrument.set_parameter(parameter, value, channel_id)
                return
        raise ParameterNotFound(f"Could not find parameter {parameter.value} in the system control {self.name}")
