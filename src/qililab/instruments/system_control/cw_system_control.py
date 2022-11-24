"""CWSystemControl class."""
from abc import ABC, abstractmethod
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, List, Tuple

import numpy as np
import scipy.integrate as integ

from qililab.constants import RUNCARD
from qililab.instruments.awg import AWG
from qililab.instruments.instruments import Instruments
from qililab.instruments.qubit_readout import QubitReadout
from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.system_control.system_control import SystemControl
from qililab.pulse import PulseSchedule
from qililab.typings import Category, SystemControlSubcategory, Parameter
from qililab.utils import Factory


@Factory.register
class CWSystemControl(SystemControl):
    """CWSystemControl class."""

    name = SystemControlSubcategory.CW_SYSTEM_CONTROL

    @dataclass(kw_only=True)
    class CWSystemControlSettings(SystemControl.SystemControlSettings):
        """CWSystemControlSettings class."""

        signal_generator: SignalGenerator
        power: float = -20
        frequencies: float = 7e9
        status: bool = False
        # awg: AWG
        def __iter__(
            self,
        ) -> Generator[Tuple[str, SignalGenerator | AWG | int], None, None]:
            """Iterate over Bus elements.

            Yields:
                Tuple[str, ]: _description_
            """
            for name, value in self.__dict__.items():
                if name in [Category.SIGNAL_GENERATOR.value]:
                    yield name, value

    settings: CWSystemControlSettings

    def set_parameter(self, parameter: Parameter, value: float, **kw):
        print(f'[CW Sys Ctrl] Called Set Parameter {kw}')
        if parameter == Parameter.FREQUENCIES:
            self.settings.frequencies = value
            print('Doing something to change frequencies')
            # self.signal_generator.device.frequencies(value)
            self.signal_generator.set_parameter(parameter=Parameter.FREQUENCY, value=value)


    def __init__(self, settings: dict, instruments: Instruments):
        super().__init__(settings=settings)
        print("created sysctrl CW")
        self._replace_settings_dicts_with_instrument_objects(instruments=instruments)

    def setup(self):
        self.signal_generator.initial_setup()
        if self.settings.status:
            self.signal_generator.start()
            print('RS ON')
        print('CW bus setup')

    def start(self):
        """Start/Turn on the instruments.
        self.signal_generator.device.start()"""
        # print('[Heterodyne SysCtrl] Entered start')
        pass

    def run(self, pulse_bus_schedule: PulseSchedule | None, nshots: int, repetition_duration: int, path: Path):
        pass

    @property
    def awg_frequencies(self):
        """SystemControl 'awg_frequencies' property."""
        return self.awg.frequencies

    @property
    def frequencies(self):
        """SystemControl 'frequencies' property."""
        return (
            self.signal_generator.frequencies - self.awg.frequencies
            if self.signal_generator.frequencies is not None
            else None
        )

    @frequencies.setter
    def frequencies(self, target_freqs: List[float]):
        """SystemControl 'frequencies' property setter."""
        self.signal_generator.frequencies = target_freqs[0] + self.awg.frequencies
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
        """Return a dict representation of the CWSystemControl class."""
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
        """String representation of the CWSystemControl class."""
        return f"{self.signal_generator}"
       
    @property
    def awg_frequency(self) -> float:
        """SystemControl 'awg_frequency' property."""

    @property
    def frequency(self) -> float:
        """SystemControl 'frequency' property."""