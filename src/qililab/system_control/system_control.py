# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""SystemControl class."""

import contextlib
from abc import ABC
from dataclasses import InitVar, dataclass
from typing import get_type_hints

from qililab.constants import RUNCARD
from qililab.instruments import AWG, Instrument, Instruments
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.qblox import QbloxModule
from qililab.pulse import PulseBusSchedule
from qililab.settings import Settings
from qililab.typings import FactoryElement
from qililab.typings.enums import Parameter, SystemControlName
from qililab.utils import Factory


@Factory.register
class SystemControl(FactoryElement, ABC):
    """SystemControl class."""

    name = SystemControlName.SYSTEM_CONTROL

    @dataclass(kw_only=True)
    class SystemControlSettings(Settings):
        """SystemControlSettings class."""

        instruments: list[Instrument]
        platform_instruments: InitVar[Instruments]

        def __post_init__(self, platform_instruments: Instruments):  # type: ignore # pylint: disable=arguments-differ
            # ``self.instruments`` contains a list of instrument aliases
            instruments = []
            for inst_alias in self.instruments:
                inst_class = platform_instruments.get_instrument(alias=inst_alias)  # type: ignore
                if inst_class is None:
                    raise NameError(
                        f"The instrument with alias {inst_alias} could not be found within the instruments of the "
                        "platform. The available instrument aliases are: "
                        f"{[inst.alias for inst in platform_instruments.elements]}."
                    )
                instruments.append(inst_class)
            self.instruments = instruments
            super().__post_init__()

    settings: SystemControlSettings

    def __init__(self, settings: dict, platform_instruments: Instruments | None = None):
        settings_class: type[self.SystemControlSettings] = get_type_hints(self).get("settings")  # type: ignore
        self.settings = settings_class(**settings, platform_instruments=platform_instruments)

    def compile(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int
    ) -> list:
        """Compiles the ``PulseBusSchedule`` into an assembly program.

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): maximum window for the duration of one hardware repetition
            num_bins (int): number of bins
        """
        for instrument in self.instruments:
            if isinstance(instrument, AWG):
                return instrument.compile(
                    pulse_bus_schedule=pulse_bus_schedule,
                    nshots=nshots,
                    repetition_duration=repetition_duration,
                    num_bins=num_bins,
                )
        raise AttributeError("The system control doesn't have any AWG to compile the given pulse sequence.")

    def upload(self, port: str):
        """Uploads any previously compiled program into the instrument."""
        for instrument in self.instruments:
            if isinstance(instrument, AWG):
                instrument.upload(port=port)
                return

        raise AttributeError("The system control doesn't have any AWG to upload a program.")

    def run(self, port: str) -> None:
        """Runs any previously uploaded program into the instrument."""
        for instrument in self.instruments:
            if isinstance(instrument, AWG):
                instrument.run(port=port)
                return

        raise AttributeError("The system control doesn't have any AWG to run a program.")

    def __str__(self):
        """String representation of a SystemControl class."""
        return "".join(f"-|{instrument}|-" for instrument in self.instruments)

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return iter(self.settings.instruments)

    def to_dict(self):
        """Return a dict representation of a SystemControl class."""
        return {RUNCARD.NAME: self.name.value, RUNCARD.INSTRUMENTS: [inst.alias for inst in self.instruments]}

    @property
    def instruments(self) -> list[Instrument]:
        """Instruments controlled by this system control."""
        return self.settings.instruments

    def set_parameter(
        self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None, port_id: str | None = None
    ):
        """Sets the parameter of a specific instrument.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
            port_id (str | None, optional): The ``port_id`` argument can be used when setting a parameter of a
                QbloxModule, to avoid having to look which sequencer corresponds to which bus.
        """
        for instrument in self.instruments:
            with contextlib.suppress(ParameterNotFound):
                if isinstance(instrument, QbloxModule):
                    instrument.setup(parameter, value, channel_id, port_id=port_id)
                else:
                    instrument.set_parameter(parameter, value, channel_id)
                return
        raise ParameterNotFound(f"Could not find parameter {parameter.value} in the system control {self.name}")

    def get_parameter(self, parameter: Parameter, channel_id: int | None = None, port_id: str | None = None):
        """Gets a parameter of a specific instrument.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        for instrument in self.instruments:
            with contextlib.suppress(ParameterNotFound):
                if isinstance(instrument, QbloxModule):
                    return instrument.get(parameter, channel_id, port_id=port_id)
                return instrument.get_parameter(parameter, channel_id)
        raise ParameterNotFound(f"Could not find parameter {parameter.value} in the system control {self.name}")
