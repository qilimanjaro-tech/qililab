"""Driver for the Drive Bus class."""
from typing import Any

from qililab.drivers.interfaces import AWG, CurrentSource, VoltageSource
from qililab.platform.components.bus_factory import BusFactory
from qililab.platform.components.interfaces import BusInterface
from qililab.pulse import PulseBusSchedule, PulseDistortion


@BusFactory.register
class FluxBus(BusInterface):
    """Qililab's driver for Flux Bus"""

    def __init__(self, awg: AWG, source: CurrentSource | VoltageSource):
        """Initialise the bus.

        Args:
            awg (AWG): Bus awg instrument
            source (CurrentSource | VoltageSource): Bus source instrument
        """
        self._awg = awg
        self.instruments: dict[str, AWG | CurrentSource | VoltageSource] = {"awg": self._awg, "source": source}
        self.delay = 0
        self.distortions: list[PulseDistortion] = []

    def execute(
        self,
        pulse_bus_schedule: PulseBusSchedule,
        nshots: int,
        repetition_duration: int,
        num_bins: int,
    ) -> None:
        """Execute a pulse bus schedule through an AWG or CurrentSource Instrument belonging to the bus.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse Bus Schedule to generate QASM program.
            nshots (int): number of shots
            repetition_duration (int): repetition duration.
            num_bins (int): number of bins
        """
        self._awg.execute(
            pulse_bus_schedule=pulse_bus_schedule,
            nshots=nshots,
            repetition_duration=repetition_duration,
            num_bins=num_bins,
        )

    def set(self, param_name: str, value: Any) -> None:
        """Set parameter on the bus' instruments.

        Args:
            param (str): Parameter's name.
            value (Any): Parameter's value
        """
        if param_name == "delay":
            self.delay = value
        elif param_name == "distortions":
            self.distortions = value
        else:
            candidates: list[AWG | CurrentSource | VoltageSource] = [
                instrument for instrument in self.instruments.values() if param_name in instrument.params
            ]
            if len(candidates) == 1:
                candidates[0].set(param_name, value)
            elif len(candidates) > 1:
                raise Exception("More than one instrument with the same parameter name found in the bus.")
            raise Exception("No instrument found in the bus for the parameter name.")

    def get(self, param_name: str) -> Any:
        """Return value associated to a parameter on the bus' instrument.

        Args:
            param (str): Parameter's name.

        Returns:
            value (Any): Parameter's value
        """
        if param_name == "delay":
            return self.delay
        if param_name == "distortions":
            return self.distortions
        candidates: list[AWG | CurrentSource | VoltageSource] = [
            instrument for instrument in self.instruments.values() if param_name in instrument.params
        ]
        if len(candidates) == 1:
            return candidates[0].get(param_name)
        if len(candidates) > 1:
            raise Exception("More than one instrument with the same parameter name found in the bus.")
        raise Exception("No instrument found in the bus for the parameter name.")
