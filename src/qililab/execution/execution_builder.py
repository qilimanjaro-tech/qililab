"""ExecutionBuilder class"""
from typing import Dict, List

from qililab.execution.bus_execution import BusExecution
from qililab.execution.buses_execution import BusesExecution
from qililab.execution.execution import Execution
from qililab.platform import Platform
from qililab.pulse import PulseSequence, PulseSequences, ReadoutPulse
from qililab.typings import BusSubcategory
from qililab.utils import Singleton


class ExecutionBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    def build(self, platform: Platform, pulse_sequences: List[PulseSequences]) -> Execution:
        """Build Execution class.

        Returns:
            Execution: Execution object.
        """

        buses_execution = self._build_buses_execution(platform=platform, pulse_sequences=pulse_sequences)

        return Execution(buses_execution=buses_execution, platform=platform)

    def _build_buses_execution(self, platform: Platform, pulse_sequences: List[PulseSequences]):
        """Loop over pulses in PulseSequence, classify them by bus index and instantiate a BusesExecution class.

        Returns:
            BusesExecution: BusesExecution object.
        """
        buses: Dict[int, BusExecution] = {}
        for idx, pulse_sequence in enumerate(pulse_sequences):
            for pulse in pulse_sequence.pulses:
                bus_subcategory = BusSubcategory.READOUT if isinstance(pulse, ReadoutPulse) else BusSubcategory.CONTROL
                bus_idx, bus = platform.get_bus(port=pulse.port, bus_subcategory=bus_subcategory)
                if bus is None:
                    raise ValueError(f"There is no bus of type {bus_subcategory.value} connected to port {pulse.port}.")
                if bus_idx not in buses:
                    pulse_sequence_tmp = PulseSequence(port=pulse.port)
                    pulse_sequence_tmp.add(pulse=pulse)
                    buses[bus_idx] = BusExecution(bus=bus, pulse_sequences=[pulse_sequence_tmp])
                    continue
                buses[bus_idx].add_pulse(pulse=pulse, idx=idx)

        return BusesExecution(buses=list(buses.values()), num_sequences=len(pulse_sequences))
