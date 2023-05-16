"""SystemControl class."""

import contextlib
from abc import ABC
from dataclasses import dataclass
from typing import get_type_hints

from qililab.constants import RUNCARD
from qililab.instruments import AWG, Instrument, Instruments
from qililab.instruments.instrument import ParameterNotFound
from qililab.platform.components.bus_element import BusElement
from qililab.pulse import PulseBusSchedule
from qililab.settings import DDBBElement
from qililab.typings.enums import Parameter, SystemControlName
from qililab.utils import Factory

# pylint: disable=super-init-not-called


@Factory.register
class SystemControl(BusElement, ABC):
    """SystemControl class."""

    name = SystemControlName.SYSTEM_CONTROL

    @dataclass(kw_only=True)
    class SystemControlSettings(DDBBElement):
        """SystemControlSettings class."""

        instrument_outputs: list[tuple[Instrument, list[int]]]  # [(Instrument, outputs), ...]

    settings: SystemControlSettings

    def __init__(self, settings: dict, platform_instruments: Instruments | None = None):
        if platform_instruments is None:
            raise ValueError("The platform instruments must be provided to initialize a SystemControl class.")
        instrument_outputs = []
        for instrument_dict in settings.pop("instruments"):
            instrument = platform_instruments.get_instrument(alias=instrument_dict["alias"])
            instrument_outputs.append((instrument, instrument_dict["outputs"]))
        settings["instrument_outputs"] = instrument_outputs
        settings_class: type[self.SystemControlSettings] = get_type_hints(self).get("settings")  # type: ignore
        self.settings = settings_class(**settings)

    def compile(self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int) -> list:
        """Compiles the ``PulseBusSchedule`` into an assembly program.

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): maximum window for the duration of one hardware repetition
        """
        for instrument, outputs in self.instrument_outputs:
            if isinstance(instrument, AWG):
                return instrument.compile(
                    pulse_bus_schedule=pulse_bus_schedule, nshots=nshots, repetition_duration=repetition_duration
                )
        raise AttributeError(
            f"The system control with alias {self.settings.alias} doesn't have any AWG to compile the given pulse "
            "sequence."
        )

    def upload(self):
        """Uploads any previously compiled program into the instrument."""
        for instrument, outputs in self.instrument_outputs:
            if isinstance(instrument, AWG):
                instrument.upload()
                return

        raise AttributeError(
            f"The system control with alias {self.settings.alias} doesn't have any AWG to upload a program."
        )

    def run(self) -> None:
        """Runs any previously uploaded program into the instrument."""
        for instrument, outputs in self.instrument_outputs:
            if isinstance(instrument, AWG):
                instrument.run()
                return

        raise AttributeError(
            f"The system control with alias {self.settings.alias} doesn't have any AWG to run a program."
        )

    def __str__(self):
        """String representation of a SystemControl class."""
        return "".join(f"-|{instrument}{outputs}|-" for instrument, outputs in self.instrument_outputs)

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return iter(self.settings.instrument_outputs)

    def to_dict(self):
        """Return a dict representation of a SystemControl class."""
        return {
            RUNCARD.ID: self.id_,
            RUNCARD.NAME: self.name.value,
            RUNCARD.CATEGORY: self.settings.category.value,
            RUNCARD.INSTRUMENTS: [
                {"alias": instrument.alias, "outputs": outputs} for instrument, outputs in self.instrument_outputs
            ],
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
    def instrument_outputs(self) -> list[tuple[Instrument, list[int]]]:
        """Instruments controlled by this system control."""
        return self.settings.instrument_outputs

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Sets the parameter of a specific instrument.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        for instrument, outputs in self.instrument_outputs:
            with contextlib.suppress(ParameterNotFound):
                instrument.set_parameter(parameter, value, channel_id)
                return
        raise ParameterNotFound(f"Could not find parameter {parameter.value} in the system control {self.name}")
