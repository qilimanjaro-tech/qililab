"""ExecutionBuilder class"""
from typing import Dict

from qililab.execution.bus_execution import BusExecution
from qililab.execution.buses_execution import BusesExecution
from qililab.execution.execution import Execution
from qililab.platform import Platform
from qililab.pulse import BusPulses, PulseSequence, ReadoutPulse
from qililab.typings import BusType
from qililab.utils import Singleton


class ExecutionBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    def build(self, platform: Platform, pulse_sequence: PulseSequence) -> Execution:
        """Build Execution class.

        Returns:
            Execution: Execution object.
        """

        buses_execution = self._build_buses_execution(platform=platform, pulse_sequence=pulse_sequence)

        return Execution(platform=platform, buses_execution=buses_execution)

    def _build_buses_execution(self, platform: Platform, pulse_sequence: PulseSequence):
        """Loop over pulses in PulseSequence, classify them by bus index and instantiate a BusesExecution class.

        Returns:
            BusesExecution: BusesExecution object.
        """
        buses: Dict[int, BusExecution] = {}
        for pulse in pulse_sequence.pulses:
            bus_type = BusType.READOUT if isinstance(pulse, ReadoutPulse) else BusType.CONTROL
            bus_idx, bus = platform.get_bus(qubit_ids=pulse.qubit_ids, bus_type=bus_type)
            if bus is None:
                raise ValueError(f"There is no bus of type {bus_type.value} connected to qubits {pulse.qubit_ids}.")
            if bus_idx not in buses:
                buses[bus_idx] = BusExecution(bus=bus, pulses=BusPulses(qubit_ids=pulse.qubit_ids, pulses=[pulse]))
                continue

            buses[bus_idx].add_pulse(pulse=pulse)

        return BusesExecution(buses=list(buses.values()))
