"""ExecutionManager class."""
from dataclasses import dataclass, field
from pathlib import Path
from threading import Thread
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np

from qililab.config import logger
from qililab.constants import RESULTSDATAFRAME
from qililab.execution.execution_buses import PulseScheduledBus
from qililab.platform.components.bus import Bus
from qililab.result import Result
from qililab.system_controls import TimeDomainReadoutSystemControl
from qililab.typings import yaml
from qililab.utils import LivePlot, Waveforms


@dataclass
class ExecutionManager:
    """ExecutionManager class."""

    num_schedules: int
    buses: list[PulseScheduledBus] = field(default_factory=list)

    def __post_init__(self):
        """check that the number of schedules matches all the schedules for each bus"""
        for bus in self.buses:
            self._check_schedules_matches(bus_num_schedules=len(bus.pulse_schedule))

    def _check_schedules_matches(self, bus_num_schedules: int):
        """check that the number of schedules matches all the schedules for each bus"""
        if bus_num_schedules != self.num_schedules:
            raise ValueError(
                f"Error: number of schedules: {self.num_schedules} does not match "
                + f"the length of the schedules in a bus: {bus_num_schedules}"
            )

    def generate_program_and_upload(self, idx: int, nshots: int, repetition_duration: int) -> None:
        """For each Bus (with a pulse schedule), translate it to an AWG program and upload it

        Args:
            idx (int): index of the pulse schedule to generate and upload
            nshots (int): number of shots / hardware average
            repetition_duration (int): maximum window for the duration of one hardware repetition
        """
        for pulse_scheduled_bus in self.buses:
            pulse_scheduled_bus.generate_program_and_upload(
                idx=idx, nshots=nshots, repetition_duration=repetition_duration
            )

    def traspile_circuit_to_buses(self):  # should take care of coordination (wait between gates and sync sequencers)
        """
        Function that converts input circuit for n qubits into m circuits one for each bus

        Args: n qubit circuit
              metadata on how qubits are mapped to buses
        Output: m circuits, one for each bus.
        """

    def run(self, plot: LivePlot | None, path: Path) -> Result | None:
        """Execute the program for each Bus (with an uploaded pulse schedule)."""

        # FIXME: run in parallel
        for bus in self.buses:
            bus.run()

        if not self.pulse_scheduled_readout_buses:
            return None

        results = [
            self._run_acquire_and_process_async_result(plot, path, readout_bus)
            for readout_bus in self.pulse_scheduled_readout_buses
        ]
        # FIXME: set multiple readout buses
        if len(results) > 1:
            logger.error("Only One Readout Bus allowed. Reading only from the first one.")
        if len(results) <= 0:
            raise ValueError("No Results acquired")
        return results[0]

    def _run_acquire_and_process_async_result(self, plot: LivePlot | None, path: Path, bus: PulseScheduledBus):
        """run a bus, acquire the result and saves and plot the results asynchronously"""
        bus.run()
        result = bus.acquire_result()
        self._asynchronous_data_handling(result=result, path=path, plot=plot)
        return result

    def _asynchronous_bus_run(self, bus: PulseScheduledBus):
        """run pulse uploaded program asynchronously"""

        def _threaded_function(bus: PulseScheduledBus):
            """Asynchronous thread."""
            bus.run()

        thread = Thread(target=_threaded_function, args=[bus])
        thread.start()

    def _asynchronous_data_handling(self, result: Result, path: Path, plot: LivePlot | None):
        """Asynchronously dumps data in file and plots the data.

        Args:
            path (Path): Filepath.
            plot (Plot | None): Plot object.
            x_value (float): Plot's x axis value.
        """

        def _threaded_function(result: Result, path: Path, plot: LivePlot | None):
            """Asynchronous thread."""
            if plot is not None:
                probs = result.probabilities()
                # get zero prob and converting to a float to plot the value
                # is a numpy.float32, so it is needed to convert it to float
                if len(probs) > 0:
                    zero_prob = float(probs[RESULTSDATAFRAME.P0].iloc[0])
                    plot.send_points(value=zero_prob)
            with open(file=path / "results.yml", mode="a", encoding="utf8") as data_file:
                result_dict = result.to_dict()
                yaml.safe_dump(data=[result_dict], stream=data_file, sort_keys=False)

        thread = Thread(target=_threaded_function, args=(result, path, plot))
        thread.start()

    def waveforms_dict(self, resolution: float = 1.0, idx: int = 0) -> Dict[int, Waveforms]:
        """Get pulses of each bus.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Dict[int, Waveforms]: Dictionary containing a list of the I/Q amplitudes of the pulses applied on each bus.
        """
        return {bus.id_: bus.waveforms(resolution=resolution, idx=idx) for bus in self.buses}

    def draw(self, resolution: float, idx: int = 0):
        """Save figure with the waveforms sent to each bus.

        Args:
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        figure, axes = plt.subplots(nrows=len(self.buses), ncols=1, sharex=True)
        if len(self.buses) == 1:
            axes = [axes]  # make axes subscriptable
        for axis_idx, (bus_idx, waveforms) in enumerate(self.waveforms_dict(resolution=resolution, idx=idx).items()):
            time = np.arange(len(waveforms)) * resolution
            axes[axis_idx].set_title(f"Bus {bus_idx}")
            axes[axis_idx].plot(time, waveforms.i, label="I")
            axes[axis_idx].plot(time, waveforms.q, label="Q")
            bus = self.buses[axis_idx]
            self._plot_acquire_time(bus=bus, sequence_idx=idx)
            axes[axis_idx].legend()
            axes[axis_idx].minorticks_on()
            axes[axis_idx].grid(which="both")
            axes[axis_idx].set_ylabel("Amplitude")
            axes[axis_idx].set_xlabel("Time (ns)")

        plt.tight_layout()
        return figure

    def _plot_acquire_time(self, bus: PulseScheduledBus, sequence_idx: int):
        """Return acquire time of bus. Return None if bus is of subcategory control.

        Args:
            bus (BusExecution): Bus execution object.
            sequence_idx (int): Pulse sequence index.

        Returns:
            int | None: Acquire time. None if bus is of subcategory control.
        """
        system_control = bus.system_control
        if isinstance(system_control, TimeDomainReadoutSystemControl):
            plt.axvline(x=system_control.acquire_time(idx=sequence_idx), color="red", label="Acquire time")

    def __iter__(self):
        """Redirect __iter__ magic method to pulse_scheduled_buses."""
        return self.buses.__iter__()

    def __getitem__(self, key):
        """Redirect __get_item__ magic method."""
        return self.buses.__getitem__(key)
