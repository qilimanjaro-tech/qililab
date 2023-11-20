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

"""LivePlot class."""
from collections.abc import Iterator
from itertools import count
from warnings import warn

import numpy as np
from qiboconnection.api import API

from qililab.typings.enums import LivePlotTypes
from qililab.utils.loop import Loop


class LivePlot:  # pylint: disable=too-many-instance-attributes
    """Class used to live plot experiment results.

    This class supports 1D and 2D plots. When running multiple sequences, the sequencer index will always be plotted
    in the x axis.

    When running loops in parallel, the plotted values will correspond to the loop with more nested loops. If all of
    them have the same amount of nested loops, the first one will be plotted.

    Args:
        connection (API): QiboConnection API object.
        num_schedules (int): Number of circuits/pulse schedules.
        title (str): Title of the plot.
        loops (list[Loop]): List of loops.
    """

    def __init__(self, connection: API, num_schedules: int, title: str = "", loops: list[Loop] | None = None):
        self.connection = connection
        self.num_schedules = num_schedules
        # We use the loop with more nested loops, or the first loop if all of them have the same amount of nested loops
        self.loop = None if loops is None else loops[np.argmax([loop.num_loops for loop in loops])]
        self.plot_dim = max(loop.num_loops for loop in loops) if loops is not None else 0
        self.plot_dim += 1 if num_schedules > 1 else 0
        if self.plot_dim not in {1, 2}:
            warn(
                message=f"The experiment contains {self.plot_dim} dimensions. Live plotting only supports 1D and 2D plots."
                " The remaining dimensions won't be plotted.",
                category=UserWarning,
            )
        self.x_values, self.y_values = self._axis_values()
        self.x_iterator, self.y_iterator = self._iterator_values()
        self.plot_id = self.create_live_plot(title=title)

    def _axis_values(self) -> tuple[list, list | None]:
        """Generate the values for the X and Y axes.

        When plotting more than one sequence, the X axis will correspond to the sequence index. Otherwise, the X axis
        will correspond to the range of the first (outer) loop.

        If there is only one loop, the Y axis will be None. Otherwise, the Y axis will correspond to the range of the
        second (inner) loop.

        Returns:
            tuple[list, list | None]: Values for the X and Y axes respectively.
        """
        if self.loop is None:
            return list(range(self.num_schedules)), None
        if self.loop.loop is None:
            if self.num_schedules == 1:
                return list(self.loop.values), None
            return list(range(self.num_schedules)), list(self.loop.values)
        return list(self.loop.loop.values), list(self.loop.values)

    def _iterator_values(self) -> tuple[Iterator, Iterator]:
        """Returns the iterators used to send data to the plot.

        Returns:
            tuple[Iterator, Iterator]: Iterators for the X and Y axis respectively.
        """
        if self.y_values is not None:
            if self.loop is not None and self.loop.num_loops >= 2:
                ranges = np.meshgrid(self.x_values, self.y_values)
                return iter(ranges[0].flatten()), iter(ranges[1].flatten())
            return iter(self.x_values), iter(self.y_values)
        return iter(self.x_values), count()

    def create_live_plot(self, title: str) -> int:
        """Create live plot.

        Args:
            title (str): Title of the plot.
        """
        return self.connection.create_liveplot(
            title=title,
            x_label=self.x_label,
            y_label=self.y_label,
            z_label=self.z_label,
            plot_type=self.plot_type.value,
            x_axis=np.array(self.x_values),
            y_axis=np.array(self.y_values) if self.y_values is not None else None,
        )

    def send_points(self, value: float):
        """Send points to the live plot.

        This function gathers the X and Y coordinates from the iterators generated in the class constructor.

        Args:
            value (float): Value to send to the plot.
        """
        if self.y_values is None:
            x_value = next(self.x_iterator)
            self.connection.send_plot_points(plot_id=self.plot_id, x=float(x_value), y=value)
            return
        x_value = next(self.x_iterator)
        y_value = next(self.y_iterator)
        self.connection.send_plot_points(
            plot_id=self.plot_id,
            x=float(x_value),
            y=float(y_value),
            z=value,
        )

    @property
    def plot_type(self) -> LivePlotTypes:
        """Return plot type.

        Returns:
            LivePlotTypes: Type of the LivePlot
        """
        return LivePlotTypes.SCATTER if self.y_values is None else LivePlotTypes.HEATMAP

    @property
    def x_label(self) -> str:
        """Create x label for live plotting.

        Returns:
            str: X label.
        """
        if self.loop is None:
            return "Sequence idx"
        if self.loop.loop is None:
            return self.label(loop=self.loop)
        return self.label(loop=self.loop.loop)

    @property
    def y_label(self):
        """Create y label for live plotting.

        Returns:
            str: Y label.
        """
        if self.loop is None:
            return "Amplitude"
        if self.loop.loop is None:
            return "Amplitude"
        return self.label(loop=self.loop)

    @property
    def z_label(self) -> str | None:
        """Create z label for live plotting.

        Returns:
            str: Z label.
        """
        return "Amplitude" if self.plot_dim == 2 else None

    def label(self, loop: Loop) -> str:
        """Return plot label from loop object.

        Args:
            loop (~utils.loop.Loop): Loop class.

        Returns:
            str: Plot label.
        """
        instrument_name = loop.alias
        return f"{instrument_name}: {loop.parameter.value} "
