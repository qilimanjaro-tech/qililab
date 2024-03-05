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

"""Bus class."""
from dataclasses import InitVar, dataclass

from qpysequence import Sequence as QpySequence

from qililab.chip import Chip, Coil, Coupler, Qubit, Resonator
from qililab.constants import BUS, NODE, RUNCARD
from qililab.instruments import Instruments, ParameterNotFound
from qililab.pulse import PulseDistortion
from qililab.result import Result
from qililab.settings import Settings
from qililab.system_control import ReadoutSystemControl, SystemControl
from qililab.typings import Parameter
from qililab.utils import Factory


class Bus:
    """Bus class.

    Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end of the bus there should be a qubit or a resonator object,
    which is connected to one or multiple qubits.

    Args:
        targets (list[Qubit | Resonator | Coupler | Coil]): Port target (or targets in case of multiple resonators).
        settings (BusSettings): Bus settings.
    """

    targets: list[Qubit | Resonator | Coupler | Coil]
    """Port target (or targets in case of multiple resonators)."""

    @dataclass
    class BusSettings(Settings):
        """Bus settings.

        Args:
            alias (str): Alias of the bus.
            system_control (SystemControl): System control used to control and readout the qubits of the bus.
            port (str): Alias of the port where bus is connected.
            distortions (list[PulseDistotion]): List of the distortions to apply to the Bus.
            delay (int): Bus delay
        """

        alias: str
        system_control: SystemControl
        port: str
        platform_instruments: InitVar[Instruments]
        distortions: list[PulseDistortion]
        delay: int

        def __post_init__(self, platform_instruments: Instruments):  # type: ignore # pylint: disable=arguments-differ
            if isinstance(self.system_control, dict):
                system_control_class = Factory.get(name=self.system_control.pop(RUNCARD.NAME))
                self.system_control = system_control_class(
                    settings=self.system_control, platform_instruments=platform_instruments
                )
            super().__post_init__()

            self.distortions = [
                PulseDistortion.from_dict(distortion) for distortion in self.distortions if isinstance(distortion, dict)  # type: ignore[arg-type]
            ]

    settings: BusSettings
    """Bus settings. Containing the alias of the bus, the system control used to control and readout its qubits, the alias
    of the port where it's connected, the list of the distortions to apply, and its delay.
    """

    def __init__(self, settings: dict, platform_instruments: Instruments, chip: Chip):
        self.settings = self.BusSettings(**settings, platform_instruments=platform_instruments)  # type: ignore
        self.targets = chip.get_port_nodes(alias=self.port)

    @property
    def alias(self):
        """Alias of the bus.

        Returns:
            str: alias of the bus
        """
        return self.settings.alias

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
    def distortions(self):
        """Bus 'distortions' property.

        Returns:
            list[PulseDistortion]: settings.distortions.
        """
        return self.settings.distortions

    @property
    def delay(self):
        """Bus 'delay' property.

        Returns:
            int: settings.delay.
        """
        return self.settings.delay

    def __str__(self):
        """String representation of a bus. Prints a drawing of the bus elements."""
        return f"Bus {self.alias}:  ----{self.system_control}---" + "".join(
            f"--|{target}|----" for target in self.targets
        )

    def __eq__(self, other: object) -> bool:
        """compare two Bus objects"""
        return str(self) == str(other) if isinstance(other, Bus) else False

    @property
    def target_freqs(self):
        """Bus 'target_freqs' property.

        Returns:
            list[float]: Frequencies of the nodes that have frequencies
        """
        return list(
            filter(None, [target.frequency if hasattr(target, NODE.FREQUENCY) else None for target in self.targets])
        )

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return iter(self.system_control)

    def to_dict(self):
        """Return a dict representation of the Bus class."""
        return {
            RUNCARD.ALIAS: self.alias,
            RUNCARD.SYSTEM_CONTROL: self.system_control.to_dict(),
            BUS.PORT: self.port,
            RUNCARD.DISTORTIONS: [distortion.to_dict() for distortion in self.distortions],
            RUNCARD.DELAY: self.delay,
        }

    def set_parameter(self, parameter: Parameter, value: int | float | str | bool, channel_id: int | None = None):
        """Set a parameter to the bus.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (int | float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        if parameter == Parameter.DELAY:
            self.settings.delay = int(value)
        else:
            try:
                self.system_control.set_parameter(
                    parameter=parameter, value=value, channel_id=channel_id, port_id=self.port, bus_alias=self.alias
                )
            except ParameterNotFound as error:
                raise ParameterNotFound(
                    f"No parameter with name {parameter.value} was found in the bus with alias {self.alias}"
                ) from error

    def get_parameter(self, parameter: Parameter, channel_id: int | None = None):
        """Gets a parameter of the bus.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (int | float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        if parameter == Parameter.DELAY:
            return self.settings.delay
        try:
            return self.system_control.get_parameter(parameter=parameter, channel_id=channel_id, port_id=self.port)
        except ParameterNotFound as error:
            raise ParameterNotFound(
                f"No parameter with name {parameter.value} was found in the bus with alias {self.alias}"
            ) from error

    def upload_qpysequence(self, qpysequence: QpySequence):
        """Uploads the qpysequence into the instrument."""
        self.system_control.upload_qpysequence(qpysequence=qpysequence, port=self.port)

    def upload(self):
        """Uploads any previously compiled program into the instrument."""
        self.system_control.upload(port=self.port)

    def run(self) -> None:
        """Runs any previously uploaded program into the instrument."""
        self.system_control.run(port=self.port)

    def acquire_result(self) -> Result:
        """Read the result from the vector network analyzer instrument

        Returns:
            Result: Acquired result
        """
        if isinstance(self.system_control, ReadoutSystemControl):
            return self.system_control.acquire_result()

        raise AttributeError(
            f"The bus {self.alias} cannot acquire results because it doesn't have a readout system control."
        )

    def acquire_qprogram_results(self, acquisitions: list[str]) -> list[Result]:
        """Read the result from the instruments

        Returns:
            list[Result]: Acquired results in chronological order
        """
        if isinstance(self.system_control, ReadoutSystemControl):
            return self.system_control.acquire_qprogram_results(acquisitions=acquisitions, port=self.port)

        raise AttributeError(
            f"The bus {self.alias} cannot acquire results because it doesn't have a readout system control."
        )
