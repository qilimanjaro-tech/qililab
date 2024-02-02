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
import contextlib
from dataclasses import InitVar, dataclass

from qpysequence import Sequence as QpySequence

from qililab.constants import RUNCARD
from qililab.instruments import (
    AWG,
    AWGAnalogDigitalConverter,
    Instrument,
    Instruments,
    ParameterNotFound,
    QuantumMachinesCluster,
)
from qililab.instruments.qblox import QbloxModule
from qililab.pulse import PulseDistortion
from qililab.result import Result
from qililab.settings import Settings
from qililab.typings import Line, Parameter
from qililab.utils import Factory


class Bus:
    """Bus class.

    Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end of the bus there should be a qubit or a resonator object,
    which is connected to one or multiple qubits.

    Args:
        settings (BusSettings): Bus settings.
    """

    @dataclass
    class BusSettings(Settings):
        """Bus settings.

        Args:
            alias (str): Alias of the bus.
            system_control (SystemControl): System control used to control and readout the qubits of the bus.
            distortions (list[PulseDistotion]): List of the distortions to apply to the Bus.
            delay (int): Bus delay
        """

        alias: str
        instruments: list[Instrument]
        channels: list[list[int | str] | None]
        qubits: list[list[int] | None]
        distortions: list[PulseDistortion]
        delay: int

        line: Line | None = None

        def __post_init__(self, platform_instruments: Instruments):  # type: ignore # pylint: disable=arguments-differ
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

            self.distortions = [
                PulseDistortion.from_dict(distortion) for distortion in self.distortions if isinstance(distortion, dict)  # type: ignore[arg-type]
            ]

    settings: BusSettings
    """Bus settings. Containing the alias of the bus, the system control used to control and readout its qubits, the
    list of the distortions to apply, and its delay.
    """

    def __init__(self, settings: dict, platform_instruments: Instruments):
        self.settings = self.BusSettings(**settings, platform_instruments=platform_instruments)  # type: ignore

    @property
    def alias(self):
        """Alias of the bus.

        Returns:
            str: alias of the bus
        """
        return self.settings.alias

    @property
    def instruments(self) -> list[Instrument]:
        """Instruments controlled by this system control."""
        return self.settings.instruments

    @property
    def channels(self) -> list[list[int | str] | None]:
        """Instruments controlled by this system control."""
        return self.settings.channels

    @property
    def qubits(self):
        """

        Returns:
            str: Qubit the bus is connected to.
        """
        return {qubit for qubits in self.settings.qubits for qubit in qubits}

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

    @property
    def line(self):
        """Bus 'delay' property.

        Returns:
            int: settings.delay.
        """
        return self.settings.line

    def __str__(self):
        """String representation of a bus. Prints a drawing of the bus elements."""
        instruments = "".join(f"-|{instrument}|-" for instrument in self.instruments)
        return f"Bus {self.alias}:  ----{instruments}----"

    def __eq__(self, other: object) -> bool:
        """compare two Bus objects"""
        return str(self) == str(other) if isinstance(other, Bus) else False

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return iter(self.instruments)

    def to_dict(self):
        """Return a dict representation of the Bus class."""
        return {
            RUNCARD.ALIAS: self.alias,
            RUNCARD.INSTRUMENTS: [instrument.alias for instrument in self.instruments],
            "channels": self.settings.channels,
            RUNCARD.DISTORTIONS: [distortion.to_dict() for distortion in self.distortions],
            RUNCARD.DELAY: self.delay,
            "qubits": self.qubits,
            "line": self.settings.line,
        }

    def is_readout(self) -> bool:
        """Return true if bus is readout bus."""
        return self.line == Line.READOUT

    def get_instrument_and_channel_of_qubit(self, qubit: int):
        """Get instrument and channel_id associated with qubit.

        Args:
            qubit (int): qubit index

        Returns:
            (_type_): A tuple o
        """
        for instrument, channel_ids, qubit_ids in zip(self.instruments, self.channels, self.qubits):
            if channel_ids is not None:
                for channel_id, qubit_id in zip(channel_ids, qubit_ids):
                    if qubit_id == qubit:
                        return instrument, channel_id
            if qubit in qubit_ids:
                return instrument, None

        return None, None

    def set_parameter(self, parameter: Parameter, value: int | float | str | bool):
        """Set a parameter to the bus.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (int | float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        if parameter == Parameter.DELAY:
            self.settings.delay = int(value)
        else:
            for instrument, channel_ids in zip(self.instruments, self.channels):
                with contextlib.suppress(ParameterNotFound):
                    if channel_ids is None:
                        instrument.set_parameter(parameter, value)
                        return
                    for channel_id in channel_ids:
                        instrument.set_parameter(parameter, value, channel_id)
                    return
            raise ParameterNotFound(
                f"No parameter with name {parameter.value} was found in the bus with alias {self.alias}"
            )

    def get_parameter(self, parameter: Parameter):
        """Gets a parameter of the bus.

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (int | float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        if parameter == Parameter.DELAY:
            return self.settings.delay
        for instrument, channel_ids in zip(self.instruments, self.channels):
            with contextlib.suppress(ParameterNotFound):
                if channel_ids is None:
                    return instrument.get_parameter(parameter)
                return instrument.get_parameter(
                    parameter, channel_ids[0]
                )  # TODO: Change this to get parameters from multiple channels
        raise ParameterNotFound(
            f"No parameter with name {parameter.value} was found in the bus with alias {self.alias}"
        )

    def upload_qpysequence(self, qpysequence: QpySequence):
        """Uploads the qpysequence into the instrument."""
        for instrument, channel_ids in zip(self.instruments, self.channels):
            if isinstance(instrument, AWG):
                if channel_ids is None:
                    instrument.upload_qpysequence(qpysequence=qpysequence, channel_id=None)
                    return
                for channel_id in channel_ids:
                    instrument.upload_qpysequence(qpysequence=qpysequence, channel_id=channel_id)
                return

        raise AttributeError("The system control doesn't have any AWG to upload a qpysequence.")

    def upload(self):
        """Uploads any previously compiled program into the instrument."""
        for instrument, channel_ids in zip(self.instruments, self.channels):
            if isinstance(instrument, AWG):
                if channel_ids is None:
                    instrument.upload(channel_id=None)
                    return
                for channel_id in channel_ids:
                    instrument.upload(channel_id=channel_id)
                return

    def run(self) -> None:
        """Runs any previously uploaded program into the instrument."""
        for instrument, channel_ids in zip(self.instruments, self.channels):
            if isinstance(instrument, AWG):
                if channel_ids is None:
                    instrument.run(channel_id=None)
                    return
                for channel_id in channel_ids:
                    instrument.run(channel_id=channel_id)
                return

    def acquire_result(self) -> Result:
        """Read the result from the vector network analyzer instrument

        Returns:
            Result: Acquired result
        """
        if self.settings.line == Line.READOUT:
            # TODO: Support acquisition from multiple instruments
            results: list[Result] = []
            for instrument in self.instruments:
                result = instrument.acquire_result()
                if result is not None:
                    results.append(result)

            if len(results) > 1:
                raise ValueError(
                    f"Acquisition from multiple instruments is not supported. Obtained a total of {len(results)} results. "
                )

            return results[0]

        raise AttributeError(
            f"The bus {self.alias} cannot acquire results because it doesn't have a readout system control."
        )

    def acquire_qprogram_results(self, acquisitions: list[str]) -> list[Result]:
        """Read the result from the instruments

        Returns:
            list[Result]: Acquired results in chronological order
        """
        if self.settings.line == Line.READOUT:
            # TODO: Support acquisition from multiple instruments
            total_results: list[list[Result]] = []
            for instrument in self.instruments:
                instrument_results = instrument.acquire_qprogram_results(acquisitions=acquisitions)
                total_results.append(instrument_results)

            return total_results[0]

        raise AttributeError(
            f"The bus {self.alias} cannot acquire results because it doesn't have a readout system control."
        )

    @property
    def acquisition_delay_time(self) -> int:
        """SystemControl 'acquisition_delay_time' property.
        Delay (in ns) between the readout pulse and the acquisition."""
        for instrument in self.instruments:
            if isinstance(instrument, AWGAnalogDigitalConverter):
                return instrument.acquisition_delay_time
        raise ValueError(f"The bus {self.alias} doesn't have an AWGAnalogDigitalConverter instrument.")
