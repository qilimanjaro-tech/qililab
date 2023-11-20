# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ExecutionManager class."""
import matplotlib.pyplot as plt
import numpy as np

from qililab.system_control import ReadoutSystemControl
from qililab.utils import Waveforms

from .bus_execution import BusExecution


# TODO: Rename to Drawer and simplify class
class ExecutionManager:  # pylint: disable=too-few-public-methods
    """ExecutionManager class.

    This class only contains drawing capabilities. The `ExecutionManager` name is maintained for backwards
    compatibility.

    At init checks that the number of schedules matches all the schedules for each bus.

    Args:
        num_schedules (int): Number of pulse schedules used in the experiment.
        buses (list[BusExecution] | None): List of buses used in the experiment.
    """

    def __init__(self, num_schedules: int, buses: list[BusExecution] | None = None):
        self.num_schedules = num_schedules
        self.buses = buses if buses is not None else []
        for bus in self.buses:
            if len(bus.pulse_bus_schedules) != self.num_schedules:
                raise ValueError(
                    f"Error: number of schedules: {self.num_schedules} does not match "
                    + f"the length of the schedules in a bus: {bus.pulse_bus_schedules}"
                )

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
            self._waveforms_dict(modulation=modulation, resolution=resolution, idx=idx).items()
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
            if isinstance(bus.system_control, ReadoutSystemControl):
                plt.axvline(x=bus.acquire_time(idx=idx), color="red", label="Acquire time")
            axes[axis_idx].minorticks_on()
            axes[axis_idx].grid(which="both")

        plt.xlabel("Time (ns)")
        plt.legend(loc="upper right")
        plt.tight_layout()
        return figure

    def _waveforms_dict(self, modulation: bool = True, resolution: float = 1.0, idx: int = 0) -> dict[str, Waveforms]:
        """Get pulses of each bus.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            dict[str, Waveforms]: Dictionary containing a list of the I/Q amplitudes of the pulses applied on each bus.
        """
        return {bus.alias: bus.waveforms(modulation=modulation, resolution=resolution, idx=idx) for bus in self.buses}
