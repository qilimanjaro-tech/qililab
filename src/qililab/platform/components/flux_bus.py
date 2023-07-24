"""Driver for the Drive Bus class."""
from typing import Any

from qililab.drivers.interfaces import AWG, CurrentSource
from qililab.platform.components.interfaces import BusInterface
from qililab.pulse import PulseBusSchedule


class FluxBus(BusInterface):
    """Qililab's driver for Flux Bus"""

    def __init__(self, source: AWG | CurrentSource, **kwargs):
        """Initialise the bus.

        Args:
            source (AWG | CurrentSource): Bus source instrument
        """
        super().__init__(**kwargs)
        self.source = source

    def execute(
        self,
        instrument_name: str,
        pulse_bus_schedule: PulseBusSchedule,
        nshots: int,
        repetition_duration: int,
        num_bins: int,
    ) -> None:
        """Execute a pulse bus schedule through an AWG or CurrentSource Instrument belonging to the bus.

        Args:
            instrument_name (str): Name of the instrument
            pulse_bus_schedule (PulseBusSchedule): Pulse Bus Schedule to generate QASM program.
            nshots (int): number of shots
            repetition_duration (int): repetition duration.
            num_bins (int): number of bins
        """
        instrument = getattr(self, instrument_name, None)
        if isinstance(instrument, AWG):
            instrument.execute(
                pulse_bus_schedule=pulse_bus_schedule,
                nshots=nshots,
                repetition_duration=repetition_duration,
                num_bins=num_bins,
            )

    def set(self, instrument_name: str, param_name: str, value: Any) -> None:
        """Set parameter on the bus' instruments.

        Args:
            instrument_name (str): Name of the instrument to set parameter on
            param (str): Parameter's name.
            value (Any): Parameter's value
        """
        instrument = getattr(self, instrument_name, None)
        if instrument:
            instrument.set(param_name, value)

    def get(self, instrument_name: str, param_name: str) -> Any:
        """Return value associated to a parameter on the bus' instrument.

        Args:
            instrument_name (str): Name of the instrument to get parameter from
            param (str): Parameter's name.
        Returns:
            value (Any): Parameter's value
        """
        param_value = None
        instrument = getattr(self, instrument_name, None)
        if instrument:
            param_value = instrument.get(param_name)

        return param_value
