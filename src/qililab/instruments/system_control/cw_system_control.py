"""CWSystemControl class."""
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
from qililab.pulse import PulseSequence
from qililab.typings import Category, SystemControlSubcategory
from qililab.utils import Factory


@Factory.register
class CWSystemControl(SystemControl):
    """CWSystemControl class."""

    name = SystemControlSubcategory.CW_SYSTEM_CONTROL

    @dataclass(kw_only=True)
    class CWSystemControlSettings(SystemControl.SystemControlSettings):
        """CWSystemControlSettings class."""

        signal_generator: SignalGenerator
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

    def __init__(self, settings: dict, instruments: Instruments):
        super().__init__(settings=settings)
        print("created sysctrl CW")
        self._replace_settings_dicts_with_instrument_objects(instruments=instruments)

    def setup(self, frequencies: List[float]):
        self.signal_generator.device.power(-20)
        # self.signal_generator.device.power(self.settings.power)
        self.signal_generator.device.frequency(7e9)
        self.signal_generator.device.on()
        print('CW bus setup')

    def start(self):
        """Start/Turn on the instruments.
        self.signal_generator.device.start()"""
        # print('[Heterodyne SysCtrl] Entered start')
        pass

    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path):
        pass

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
        return f"{self.awg}|----|{self.signal_generator}"