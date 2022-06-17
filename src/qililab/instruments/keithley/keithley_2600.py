"""Keithley2600 instrument."""
import xarray

from qililab.instruments.instrument import Instrument
from qililab.typings import BusElementName, Keithley2600Driver
from qililab.utils import nested_dataclass


class Keithley2600(Instrument):
    """Keithley2600 class."""

    name = BusElementName.KEITHLEY

    @nested_dataclass
    class Keithley2600Settings(Instrument.InstrumentSettings):
        """Settings for Keithley2600 instrument."""

    # TODO: This instruments contains two independent instruments inside: 'device.smua' and 'device.smub'.
    # Right now we only use smua. Discuss how to handle them.

    settings: Keithley2600Settings
    device: Keithley2600Driver

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = self.Keithley2600Settings(**settings)

    @Instrument.CheckConnected
    def setup(self):
        """Setup instrument."""

    @Instrument.CheckConnected
    def start(self):
        """Start generating microwaves."""

    @Instrument.CheckConnected
    def stop(self):
        """Stop generating microwaves."""

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        self.device = Keithley2600Driver(f"{self.name.value}_{self.id_}", f"TCPIP0::{self.ip}::inst0::INSTR")

    def reset(self):
        """Reset instrument."""
        self.device.reset()

    def fast_sweep(self, start: float, stop: float, steps: int, mode: str) -> xarray.Dataset:
        """Perform a fast sweep using a deployed lua script and return an xarray dataset.

        Args:
            start: starting sweep value (V or A)
            stop: end sweep value (V or A)
            steps: number of steps
            mode: Type of sweep, either 'IV' (voltage sweep), 'VI' (current sweep two probe setup) or 'VIfourprobe'
            (current sweep four probe setup)

        Returns:
            xarray.Dataset: Measured data.
        """
        data = self.device.smua.doFastSweep(start=start, stop=stop, steps=steps, mode=mode)
        return data.to_xarray()
