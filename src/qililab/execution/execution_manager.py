"""ExecutionManager class."""
from dataclasses import dataclass, field
from queue import Queue

import matplotlib.pyplot as plt
import numpy as np

from qililab.config import logger
from qililab.platform import Platform
from qililab.result import Result
from qililab.system_control import ReadoutSystemControl
from qililab.utils import Waveforms

from .bus_execution import BusExecution


@dataclass
class ExecutionManager:
    """ExecutionManager class."""

    num_schedules: int
    platform: Platform
    buses: list[BusExecution] = field(default_factory=list)

    def turn_on_instruments(self):
        """Start/Turn on the instruments."""
        self.platform.turn_on_instruments()

    def turn_off_instruments(self):
        """Start/Turn on the instruments."""
        self.platform.turn_off_instruments()

    def __post_init__(self):
        """check that the number of schedules matches all the schedules for each bus"""
        for bus in self.buses:
            self._check_schedules_matches(bus_num_schedules=len(bus.pulse_bus_schedules))

    def _check_schedules_matches(self, bus_num_schedules: int):
        """check that the number of schedules matches all the schedules for each bus"""
        if bus_num_schedules != self.num_schedules:
            raise ValueError(
                f"Error: number of schedules: {self.num_schedules} does not match "
                + f"the length of the schedules in a bus: {bus_num_schedules}"
            )

    def compile(self, idx: int, nshots: int, repetition_duration: int, num_bins: int) -> dict:
        """Compiles the pulse schedule at index ``idx`` of each bus into a set of assembly programs.

        Args:
            idx (int): index of the circuit to compile and upload
            nshots (int): number of shots / hardware average
            repetition_duration (int): maximum window for the duration of one hardware repetition
            num_bins (int): number of bins

        Returns:
            list: list of compiled assembly programs
        """
        programs = {}
        for bus in self.buses:
            bus_programs = bus.compile(
                idx=idx, nshots=nshots, repetition_duration=repetition_duration, num_bins=num_bins
            )
            programs[bus.alias] = bus_programs
        return programs

    def upload(self):
        """Uploads all previously compiled programs into its corresponding instruments."""
        for bus in self.buses:
            bus.upload()

    def run(self, queue: Queue) -> Result | None:
        """Execute the program for each Bus (with an uploaded pulse schedule)."""

        for bus in self.buses:
            bus.run()

        results = []
        for bus in self.readout_buses:
            result = bus.acquire_result()
            queue.put_nowait(item=result)
            results.append(result)

        # FIXME: set multiple readout buses
        if len(results) > 1:
            logger.error("Only One Readout Bus allowed. Reading only from the first one.")
        if not results:
            raise ValueError("No Results acquired")
        return results[0]

    def waveforms_dict(self, modulation: bool = True, resolution: float = 1.0, idx: int = 0) -> dict[str, Waveforms]:
        """Get pulses of each bus.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            dict[str, Waveforms]: Dictionary containing a list of the I/Q amplitudes of the pulses applied on each bus.
        """
        return {bus.alias: bus.waveforms(modulation=modulation, resolution=resolution, idx=idx) for bus in self.buses}

    def draw(  # pylint: disable=too-many-locals
        self,
        real: bool = True,
        imag: bool = True,
        absolute: bool = False,
        modulation: bool = True,
        linestyle: str = "-",
        resolution: float = 1.0,
        idx: int = 0,
    ):
        """Save figure with the waveforms/envelopes sent to each bus.

        You can plot any combination of the real (blue), imaginary (orange) and absolute (green) parts of the function.

        Args:
            Args:
            real (bool): True to plot the real part of the function, False otherwise. Default to True.
            imag (bool): True to plot the imaginary part of the function, False otherwise. Default to True.
            absolute (bool): True to plot the absolute of the function, False otherwise. Default to False.
            modulation (bool): True to plot the modulated wave form, False for only envelope. Default to True.
            linestyle (str): lineplot ("-", "--", ":"), point plot (".", "o", "x") or any other linestyle matplotlib accepts. Defaults to "-".
            resolution (float, optional): The resolution of the pulses in ns. Defaults to 1.0.

        Returns:
            Figure: Matplotlib figure with the waveforms sent to each bus.
        """
        figure, axes = plt.subplots(nrows=len(self.buses), ncols=1, sharex=True)
        plt.ylabel("Amplitude")
        figure.suptitle(" Pulses on each bus ", fontsize=20)

        if len(self.buses) == 1:
            axes = [axes]  # make axes subscriptable

        for axis_idx, (bus_alias, waveforms) in enumerate(
            self.waveforms_dict(modulation=modulation, resolution=resolution, idx=idx).items()
        ):
            time = np.arange(len(waveforms)) * resolution
            axes[axis_idx].set_title(f"Bus {bus_alias}", loc="right")

            if imag:
                axes[axis_idx].plot(time, waveforms.q, linestyle, label="imag", color="orange")

            if real:
                axes[axis_idx].plot(time, waveforms.i, linestyle, label="real", color="blue")

            if absolute:
                waveform_abs = np.sqrt(waveforms.q * waveforms.q + waveforms.i * +waveforms.i)
                axes[axis_idx].plot(time, waveform_abs, linestyle, label="abs", color="green")

            bus = self.buses[axis_idx]
            self._plot_acquire_time(bus=bus, sequence_idx=idx)
            axes[axis_idx].minorticks_on()
            axes[axis_idx].grid(which="both")

        plt.xlabel("Time (ns)")
        plt.legend(loc="upper right")
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
    def readout_buses(self) -> list[BusExecution]:
        """Returns a list of all the readout buses.

        Returns:
            list[BusExecution]: list of readout buses
        """
        return [bus for bus in self.buses if isinstance(bus.system_control, ReadoutSystemControl)]
