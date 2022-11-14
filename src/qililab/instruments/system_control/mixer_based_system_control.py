"""MixerBasedSystemControl class."""
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, List, Tuple

import numpy as np

from qililab.constants import RUNCARD
from qililab.instruments.awg import AWG
from qililab.instruments.instruments import Instruments
from qililab.instruments.qubit_readout import QubitReadout
from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.system_control.system_control import SystemControl
from qililab.pulse import PulseSequence
from qililab.typings import Category, SystemControlSubcategory
from qililab.typings.enums import Parameter
from qililab.utils import Factory


@Factory.register
class MixerBasedSystemControl(SystemControl):
    """MixerBasedSystemControl class."""

    name = SystemControlSubcategory.MIXER_BASED_SYSTEM_CONTROL

    @dataclass(kw_only=True)
    class MixerBasedSystemControlSettings(SystemControl.SystemControlSettings):
        """MixerBasedSystemControlSettings class."""

        awg: AWG
        signal_generator: SignalGenerator

        def __iter__(
            self,
        ) -> Generator[Tuple[str, SignalGenerator | AWG | int], None, None]:
            """Iterate over Bus elements.

            Yields:
                Tuple[str, ]: _description_
            """
            for name, value in self.__dict__.items():
                if name in [Category.AWG.value, Category.SIGNAL_GENERATOR.value]:
                    yield name, value

    settings: MixerBasedSystemControlSettings

    def __init__(self, settings: dict, instruments: Instruments):
        super().__init__(settings=settings)
        self._replace_settings_dicts_with_instrument_objects(instruments=instruments)

    def setup(self, frequencies: List[float]):
        """Setup instruments."""
        min_freq = np.min(frequencies)
        self.signal_generator.frequency = min_freq + self.awg.frequency
        self.awg.frequencies = list(self.signal_generator.frequency - np.array(frequencies))
        self.awg.setup()
        self.signal_generator.setup()

    def start(self):
        """Start/Turn on the instruments."""
        self.signal_generator.start()

    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path):
        """Change the SignalGenerator frequency if needed and run the given pulse sequence."""
        if pulse_sequence.frequency is not None and pulse_sequence.frequency != self.frequency:
            # FIXME: find the channel associated to the port of a pulse
            self._update_frequency(frequency=pulse_sequence.frequency, channel_id=0)
        return self.awg.run(
            pulse_sequence=pulse_sequence,
            nshots=nshots,
            repetition_duration=repetition_duration,
            path=path,
        )

    def _update_frequency(self, frequency: float, channel_id: int | None = None):
        """update frequency to the signal generator and AWG

        Args:
            frequency (float): the bus final frequency (AWG + Signal Generator)
            channel_id (int | None, optional): AWG Channel. Defaults to None.
        """
        if channel_id is None:
            raise ValueError("channel not specified to update instrument")
        if channel_id > self.awg.num_sequencers - 1:
            raise ValueError(
                f"the specified channel_id:{channel_id} is out of range. "
                + f"Number of sequencers is {self.awg.num_sequencers}"
            )
        signal_generator_frequency = frequency - self.awg.frequencies[channel_id]
        self.signal_generator.set_parameter(parameter=Parameter.FREQUENCY, value=signal_generator_frequency)

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set parameter for an instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        if parameter.value == Parameter.POWER.value:
            self.signal_generator.set_parameter(parameter=parameter, value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.FREQUENCY.value:
            if not isinstance(value, float):
                raise ValueError(f"value must be a float. Current type: {type(value)}")
            self._update_frequency(frequency=value, channel_id=channel_id)
            return
        # the rest of parameters are assigned to the AWG
        self.awg.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

    @property
    def awg_frequency(self):
        """SystemControl 'awg_frequency' property."""
        return self.awg.frequency

    @property
    def frequency(self):
        """SystemControl 'frequency' property."""
        return (
            self.signal_generator.frequency - self.awg.frequency
            if self.signal_generator.frequency is not None
            else None
        )

    @frequency.setter
    def frequency(self, target_freqs: List[float]):
        """SystemControl 'frequency' property setter."""
        self.signal_generator.frequency = target_freqs[0] + self.awg.frequency
        self.signal_generator.setup()

    @property
    def signal_generator(self):
        """Bus 'signal_generator' property.
        Returns:
            SignalGenerator: settings.signal_generator.
        """
        return self.settings.signal_generator

    @property
    def awg(self):
        """Bus 'awg' property.
        Returns:
            (QubitControl | None): settings.qubit_control.
        """
        return self.settings.awg

    @property
    def acquisition_delay_time(self) -> int:
        """SystemControl 'acquisition_delay_time' property.
        Delay (in ns) between the readout pulse and the acquisition."""
        if isinstance(self.awg, QubitReadout):
            return self.awg.acquisition_delay_time
        raise ValueError("AWG is not a QubitReadout instance.")

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.settings.__iter__()

    def to_dict(self):
        """Return a dict representation of the MixerBasedSystemControl class."""
        return {
            RUNCARD.ID: self.id_,
            RUNCARD.CATEGORY: self.settings.category.value,
            RUNCARD.SUBCATEGORY: self.settings.subcategory.value,
        } | {key: value.alias for key, value in self}

    def _replace_settings_dicts_with_instrument_objects(self, instruments: Instruments):
        """Replace dictionaries from settings into its respective instrument classes."""
        for name, value in self.settings:
            if isinstance(value, str):
                instrument_object = instruments.get_instrument(alias=value)
                setattr(self.settings, name, instrument_object)

    def __str__(self):
        """String representation of the MixerBasedSystemControl class."""
        return f"{self.awg}|----|{self.signal_generator}"
