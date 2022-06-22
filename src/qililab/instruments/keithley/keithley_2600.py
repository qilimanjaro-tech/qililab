"""Keithley2600 instrument."""
from typing import Tuple

import numpy as np

from qililab.instruments.instrument import Instrument
from qililab.typings import InstrumentName, Keithley2600Driver
from qililab.utils import nested_dataclass


class Keithley2600(Instrument):
    """Keithley2600 class."""

    name = InstrumentName.KEITHLEY2600

    @nested_dataclass
    class Keithley2600Settings(Instrument.InstrumentSettings):
        """Settings for Keithley2600 instrument."""

        max_current: float
        max_voltage: float

    # TODO: This instruments contains two independent instruments inside: 'device.smua' and 'device.smub'.
    # Right now we only use smua. Discuss how to handle them.

    settings: Keithley2600Settings
    device: Keithley2600Driver

    @Instrument.CheckConnected
    def setup(self):
        """Setup instrument."""
        self.device.smua.limiti(self.max_current)
        self.device.smua.limitv(self.max_voltage)

    @Instrument.CheckConnected
    def start(self):
        """Start generating microwaves."""

    @Instrument.CheckConnected
    def stop(self):
        """Stop generating microwaves."""

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = Keithley2600Driver(
            name=f"{self.name.value}_{self.id_}", address=f"TCPIP0::{self.ip}::INSTR", visalib="@py"
        )

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
        """Keithley2600 'max_current' property.

        Returns:
            float: Maximum current allowed in voltage mode.
        """
        return self.settings.max_current

    @max_current.setter
    def max_current(self, value):
        """Keithley2600 'max_current' setter property.

        Args:
            float: Maximum current allowed in voltage mode.
        """
        self.settings.max_current = value
        self.setup()

    @property
    def max_voltage(self):
        """Keithley2600 'max_voltage' property.

        Returns:
            float: Maximum voltage allowed in current mode.
        """
        return self.settings.max_voltage

    @max_voltage.setter
    def max_voltage(self, value):
        """Keithley2600 'max_voltage' setter property.

        Args:
            float: Maximum voltage allowed in current mode.
        """
        self.settings.max_voltage = value
        self.setup()
