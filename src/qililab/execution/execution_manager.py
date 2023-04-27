"""ExecutionManager class."""
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import List

import matplotlib.pyplot as plt
import numpy as np

from qililab.config import logger
from qililab.constants import RESULTSDATAFRAME
from qililab.execution import BusExecution
from qililab.platform import Platform
from qililab.result import Result
from qililab.system_control import ReadoutSystemControl
from qililab.typings import yaml
from qililab.utils import LivePlot, Waveforms


@dataclass
class ExecutionManager:
    """ExecutionManager class."""

    num_schedules: int
    platform: Platform
    buses: List[BusExecution] = field(default_factory=list)
    program_duration: float = field(init=False)

    def turn_on_instruments(self):
        """Start/Turn on the instruments."""
        self.platform.turn_on_instruments()

    def turn_off_instruments(self):
        """Start/Turn on the instruments."""
        self.platform.turn_off_instruments()

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

    def compile(self, idx: int, nshots: int, repetition_duration: int) -> dict:
        """Compiles the pulse schedule at index ``idx`` of each bus into a set of assembly programs.

        Args:
            idx (int): index of the circuit to compile and upload
            nshots (int): number of shots / hardware average
            repetition_duration (int): maximum window for the duration of one hardware repetition

        Returns:
            list: list of compiled assembly programs
        """
        programs = {}
        for bus in self.buses:
            bus_programs = bus.compile(idx=idx, nshots=nshots, repetition_duration=repetition_duration)
            programs[bus.alias] = bus_programs
        # we save the duration of the program (in seconds) to use it as a timeout for the queue
        self.program_duration = repetition_duration * nshots * 1e-9
        return programs

    def upload(self):
        """Uploads all previously compiled programs into its corresponding instruments."""
        for bus in self.buses:
            bus.upload()

    def run(self, plot: LivePlot | None, path: Path) -> Result | None:
        """Execute the program for each Bus (with an uploaded pulse schedule)."""

        for bus in self.buses:
            bus.run()

        data_queue: Queue = Queue()  # queue used to store the experiment results
        self._asynchronous_data_handling(queue=data_queue, path=path, plot=plot)

        results = []
        for bus in self.readout_buses:
            result = bus.acquire_result()
            data_queue.put_nowait(item=result)
            results.append(result)

        # FIXME: set multiple readout buses
        if len(results) > 1:
            logger.error("Only One Readout Bus allowed. Reading only from the first one.")
        if not results:
            raise ValueError("No Results acquired")
        return results[0]

    def _asynchronous_data_handling(self, queue: Queue, path: Path, plot: LivePlot | None):
        """Starts a thread that asynchronously gets the results from the queue, sends them to the live plot (if any)
        and saves them to a file.

        If no items are received in the queue for 5 seconds, the thread will exit.

        Args:
            queue (Queue): Queue used to store the experiment results.
            path (Path): Path where the results will be saved.
            plot (LivePlot, optional): Live plot to send the results to. Defaults to None.
        """

        def _threaded_function():
            """Asynchronous thread."""
            while True:
                try:
                    result = queue.get(timeout=10 * self.program_duration)  # get new result from the queue
                except Empty:
                    return  # exit thread if no results are received for 10 times the duration of the program

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

        thread = Thread(target=_threaded_function)
        thread.start()

    def waveforms_dict(self, resolution: float = 1.0, idx: int = 0) -> dict[int, Waveforms]:
        """Get pulses of each bus.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            dict[int, Waveforms]: Dictionary containing a list of the I/Q amplitudes of the pulses applied on each bus.
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

    def _plot_acquire_time(self, bus: BusExecution, sequence_idx: int):
        """Return acquire time of bus. Return None if bus is of subcategory control.

        Args:
            bus (BusExecution): Bus execution object.
            sequence_idx (int): Pulse sequence index.

        Returns:
            int | None: Acquire time. None if bus is of subcategory control.
        """
        if isinstance(bus.system_control, ReadoutSystemControl):
            plt.axvline(x=bus.acquire_time(idx=sequence_idx), color="red", label="Acquire time")

    def __iter__(self):
        """Redirect __iter__ magic method to buses."""
        return self.buses.__iter__()

    def __getitem__(self, key):
        """Redirect __get_item__ magic method."""
        return self.buses.__getitem__(key)

    @property
    def readout_buses(self) -> List[BusExecution]:
        """Returns a list of all the readout buses.

        Returns:
            List[BusExecution]: list of readout buses
        """
        return [bus for bus in self.buses if isinstance(bus.system_control, ReadoutSystemControl)]
