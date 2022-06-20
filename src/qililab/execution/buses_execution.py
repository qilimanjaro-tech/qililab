"""BusesExecution class."""

import itertools
from dataclasses import dataclass, field
from pathlib import Path
from threading import Thread
from typing import List

import matplotlib.pyplot as plt
import numpy as np
from tqdm.auto import tqdm

from qililab.execution.bus_execution import BusExecution
from qililab.result import Result
from qililab.typings import BusSubcategory, yaml
from qililab.utils import LivePlot


@dataclass
class BusesExecution:
    """BusesExecution class."""

    num_sequences: int
    buses: List[BusExecution] = field(default_factory=list)

    def connect(self):
        """Connect to the instruments."""
        for bus in self.buses:
            bus.connect()

    def setup(self):
        """Setup instruments with experiment settings."""
        for bus in self.buses:
            bus.setup()

    def start(self):
        """Start/Turn on the instruments."""
        for bus in self.buses:
            bus.start()

    def run(
        self, nshots: int, repetition_duration: int, software_average: int, plot: LivePlot | None, path: Path
    ) -> List[Result]:
        """Run the given pulse sequence."""
        results: List[Result] = []
        disable = self.num_sequences == 1
        for idx, _ in itertools.product(
            tqdm(range(self.num_sequences), desc="Sequences", leave=False, disable=disable), range(software_average)
        ):
            for bus in self.buses:
                result = bus.run(nshots=nshots, repetition_duration=repetition_duration, idx=idx, path=path)
                if result is not None:
                    results.append(result)
                    self._asynchronous_data_handling(result=result, path=path, plot=plot, x_value=idx)

        return results

    def _asynchronous_data_handling(self, result: Result, path: Path, plot: LivePlot | None, x_value: float):
        """Asynchronously dumps data in file and plots the data.

        Args:
            path (Path): Filepath.
            plot (Plot | None): Plot object.
            x_value (float): Plot's x axis value.
        """

        def _threaded_function(result: Result, path: Path, plot: LivePlot | None, x_value: float):
            """Asynchronous thread."""
            with open(file=path / "results.yml", mode="a", encoding="utf8") as data_file:
                yaml.safe_dump(data=[result.to_dict()], stream=data_file, sort_keys=False)
            if plot is not None:
                plot.send_points(x_value=x_value, y_value=result.probabilities()[0])

        thread = Thread(target=_threaded_function, args=(result, path, plot, x_value))
        thread.start()

    def close(self):
        """Close connection to the instruments."""
        for bus in self.buses:
            bus.close()

    def waveforms(self, resolution: float = 1.0, idx: int = 0):
        """Get pulses of each bus.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Dict[int, np.ndarray]: Dictionary containing a list of the I/Q amplitudes of the pulses applied on each bus.
        """
        return {bus.id_: np.array(bus.waveforms(resolution=resolution, idx=idx)) for bus in self.buses}

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
        for axis_idx, (bus_idx, pulse) in enumerate(self.waveforms(resolution=resolution, idx=idx).items()):
            time = np.arange(len(pulse[0])) * resolution
            axes[axis_idx].set_title(f"Bus {bus_idx}")
            axes[axis_idx].plot(time, pulse[0], label="I")
            axes[axis_idx].plot(time, pulse[1], label="Q")
            bus = self.buses[axis_idx]
            self._plot_acquire_time(bus=bus, sequence_idx=idx)
            axes[axis_idx].legend()
            axes[axis_idx].minorticks_on()
            axes[axis_idx].grid(which="both")
            axes[axis_idx].set_ylabel("Amplitude")
            axes[axis_idx].set_xlabel("Time (ns)")

        plt.tight_layout()
        # plt.savefig("test.png")
        return figure

    def _plot_acquire_time(self, bus: BusExecution, sequence_idx: int):
        """Return acquire time of bus. Return None if bus is of subcategory control.

        Args:
            bus (BusExecution): Bus execution object.
            sequence_idx (int): Pulse sequence index.

        Returns:
            int | None: Acquire time. None if bus is of subcategory control.
        """
        if bus.subcategory == BusSubcategory.READOUT:
            plt.axvline(x=bus.acquire_time(idx=sequence_idx), color="red", label="Acquire time")

    def __iter__(self):
        """Redirect __iter__ magic method to buses."""
        return self.buses.__iter__()

    def __getitem__(self, key):
        """Redirect __get_item__ magic method."""
        return self.buses.__getitem__(key)
