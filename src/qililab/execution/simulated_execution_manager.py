"""Simulated ExecutionManager class."""
from dataclasses import dataclass, field
from pathlib import Path

from qililab.config import logger
from qililab.execution.execution_buses.simulated_pulse_scheduled_readout_bus import (
    SimulatedPulseScheduledReadoutBus,
)
from qililab.execution.execution_manager import ExecutionManager
from qililab.result import Result
from qililab.utils import LivePlot


@dataclass
class SimulatedExecutionManager(ExecutionManager):
    """Simulated ExecutionManager class."""

    simulated_pulse_scheduled_buses: list[SimulatedPulseScheduledReadoutBus] = field(default_factory=list)

    @property
    def all_pulse_scheduled_buses(self):
        """returns a list with only simulated_pulse_scheduled_buses"""
        return self.simulated_pulse_scheduled_buses

    def generate_program_and_upload(self, idx: int, nshots: int, repetition_duration: int, path: Path) -> None:
        """For each Bus (with a pulse schedule), translate it to an AWG program and upload it

        Args:
            idx (int): index of the pulse schedule to compile and upload
            nshots (int): number of shots / hardware average
            repetition_duration (int): maximum window for the duration of one hardware repetition
            path (Path): path to save the program to upload
        """
        for simulated_bus in self.simulated_pulse_scheduled_buses:
            simulated_bus.generate_program(schedule_index_to_load=idx)

    def run(self, plot: LivePlot | None, path: Path) -> Result | None:
        """Execute the program for each Bus (with an uploaded pulse schedule)."""

        results = [
            self._simulated_run_acquire_and_process_async_result(plot, path, simulated_bus)
            for simulated_bus in self.simulated_pulse_scheduled_buses
        ]
        # FIXME: set multiple readout buses
        if len(results) > 1:
            logger.error("Only One Simulated Readout Bus allowed. Reading only from the first one.")
        if len(results) <= 0:
            raise ValueError("No Results acquired")
        return results[0]

    def _simulated_run_acquire_and_process_async_result(
        self, plot: LivePlot | None, path: Path, simulated_bus: SimulatedPulseScheduledReadoutBus
    ):
        """run a bus, acquire the result and saves and plot the results asynchronously"""
        simulated_bus.run()
        result = simulated_bus.acquire_result()
        self._asynchronous_data_handling(result=result, path=path, plot=plot)
        return result
