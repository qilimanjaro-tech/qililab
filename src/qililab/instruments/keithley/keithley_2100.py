"""Keithley2100 instrument."""
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from qililab.instruments.instrument import Instrument
from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName, Keithley2100Driver


@InstrumentFactory.register
class Keithley2100(Instrument):
    """Keithley2100 class.
    Args:
        name (InstrumentName): name of the instrument
        device (Keithley2100Driver): Instance of the Instrument device driver.
        settings (Keithley2100Settings): Settings of the instrument.
    """

    name = InstrumentName.KEITHLEY2100

    @dataclass
    class Keithley2100Settings(Instrument.InstrumentSettings):
        """Settings for Keithley2100 instrument."""

        max_current: float
        max_voltage: float

    # TODO: This instruments contains two independent instruments inside: 'device.smua' and 'device.smub'.
    # Right now we only use smua. Discuss how to handle them.

    settings: Keithley2100Settings
    device: Keithley2100Driver

    @Instrument.CheckDeviceInitialized
    def setup(self):
        """Setup instrument."""

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """performs an initial setup.
        For this instrument it is the same as a regular setup"""
        self.setup()

    @Instrument.CheckDeviceInitialized
    def start(self):
        """Start generating microwaves."""

    @Instrument.CheckDeviceInitialized
    def stop(self):
        """Stop generating microwaves."""

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        self.device.reset()

    def fast_sweep(self, start: float, stop: float, steps: int, mode: str) -> Tuple[np.ndarray, np.ndarray]:
        """Perform a fast sweep using a deployed lua script and return an xarray dataset.

        Args:
            start: starting sweep value (V or A)
            stop: end sweep value (V or A)
            steps: number of steps
            mode: Type of sweep, either 'IV' (voltage sweep), 'VI' (current sweep two probe setup) or 'VIfourprobe'
            (current sweep four probe setup)

        Returns:
            np.ndarray: Measured data.
        """
        data = self.device.smua.doFastSweep(start=start, stop=stop, steps=steps, mode=mode)
        x_values = np.linspace(start=start, stop=stop, num=steps)
        return x_values, data.to_xarray().to_array().values.squeeze()

    @property
    def max_current(self):
        """Keithley2100 'max_current' property.

        Returns:
            float: Maximum current allowed in voltage mode.
        """
        return self.settings.max_current

    @max_current.setter
    def max_current(self, value):
        """Keithley2100 'max_current' setter property.

        Args:
            float: Maximum current allowed in voltage mode.
        """
        self.device.smua.limiti(value)
        self.settings.max_current = value

    @property
    def max_voltage(self):
        """Keithley2100 'max_voltage' property.

        Returns:
            float: Maximum voltage allowed in current mode.
        """
        return self.settings.max_voltage

    @max_voltage.setter
    def max_voltage(self, value):
        """Keithley2100 'max_voltage' setter property.

        Args:
            float: Maximum voltage allowed in current mode.
        """
        self.device.smua.limitv(value)
        self.settings.max_voltage = value
