"""ExecutionBuilder class"""
from typing import List

from qililab.execution.bus_execution import BusExecution
from qililab.execution.buses_execution import BusesExecution
from qililab.execution.execution import Execution
from qililab.platform import Bus, BusControl, BusReadout, Platform
from qililab.pulse import PULSE_BUILDER, Pulse
from qililab.pulse.pulse_sequence import PulseSequence
from qililab.typings import Category
from qililab.utils import Singleton


class ExecutionBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    def build(self, platform: Platform, pulses: List[Pulse]) -> Execution:
        """Build Execution class.

        Returns:
            Execution: Execution object.
        """

        control_pulse_sequences, readout_pulse_sequences = PULSE_BUILDER.build(pulses=pulses)

        buses: List[BusExecution] = []
        for pulse_sequences in (control_pulse_sequences, readout_pulse_sequences):
            buses.extend(
                self._build_bus_execution(qubit_id=qubit_id, pulse_sequence=pulse_sequence, platform=platform)
                for qubit_id, pulse_sequence in pulse_sequences.items()
            )

        buses_execution = BusesExecution(buses=buses)

        return Execution(platform=platform, buses_execution=buses_execution)

    def _build_bus_execution(self, qubit_id: int, platform: Platform, pulse_sequence: PulseSequence) -> BusExecution:
        """Build BusExecution object.

        Args:
            bus_execution_settings (dict): Dictionary containing the settings of the BusExecution object.

        Returns:
            BusExecution: BusExecution object.
        """
        _, bus_idxs = platform.get_element(category=Category.QUBIT, id_=qubit_id)

        if not bus_idxs:
            raise ValueError(f"Qubit with id {qubit_id} is not defined in the platform.")

        bus: Bus | None = None
        for bus_idx in bus_idxs:
            bus_tmp = platform.buses[bus_idx]
            if (isinstance(bus_tmp, BusControl) and pulse_sequence.readout is False) or (
                isinstance(bus_tmp, BusReadout) and pulse_sequence.readout is True
            ):
                bus = bus_tmp

        if bus is None:
            literal = "readout" if pulse_sequence.readout else "control"
            raise ValueError(f"Qubit with id {qubit_id} is not connected to a {literal} bus.")

        return BusExecution(bus=bus, pulse_sequence=pulse_sequence)
