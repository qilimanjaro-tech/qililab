"""LivePlot class."""
from collections.abc import Iterator
from itertools import count

import numpy as np
from qiboconnection.api import API

from qililab.typings.enums import LivePlotTypes
from qililab.utils.loop import Loop


class LivePlot:
    """Class used to live plot experiment results.

    This class supports 1D and 2D plots. When running multiple sequences, the sequencer index will always be plotted
    in the x axis.

    Args:
        connection (API): QiboConnection API object.
        num_schedules (int): Number of circuits/pulse schedules.
        title (str): Title of the plot.
        loops (list[Loop]): List of loops.
    """

    def __init__(self, connection: API, num_schedules: int, title: str = "", loops: list[Loop] | None = None):
        self.connection = connection
        self.num_schedules = num_schedules
        self.all_loops = [] if loops is None else [inner_loop for loop in loops for inner_loop in loop.loops]
        # Flatten all parallel and inner loops
        if len(self.all_loops) > 2:
            raise ValueError(
                f"Cannot create a live plot with {len(self.all_loops)} loops. Only 1D and 2D plots are supported."
            )
        if not self.all_loops and num_schedules == 1:
            raise ValueError("Cannot create a live plot with 1 pulse schedule and no loops.")
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
        if self.num_schedules > 1:
            x_values = list(range(self.num_schedules))
            return x_values, None if len(self.all_loops) == 0 else list(self.all_loops[0].range)
        x_values = list(self.all_loops[0].range)
        if len(self.all_loops) == 1:
            return x_values, None
        y_values = list(self.all_loops[1].range)
        return x_values, y_values

    def _iterator_values(self) -> tuple[Iterator, Iterator]:
        """Returns the iterators used to send data to the plot.

        Returns:
            tuple[Iterator, Iterator]: Iterators for the X and Y axis respectively.
        """
        if self.y_values is not None:
            ranges = np.meshgrid(self.x_values, self.y_values)
            return iter(ranges[0].flatten()), iter(ranges[1].flatten())
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
            y_axis=np.array(self.y_values) or None,
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
    def y_label(self):
        """Create y label for live plotting.

        Returns:
            str: Y label.
        """
        if self.y_values is not None:
            return self.label(loop=self.all_loops[1])

        return "Amplitude"

    @property
    def z_label(self) -> str | None:
        """Create z label for live plotting.

        Returns:
            str: Z label.
        """
        return "Amplitude" if len(self.all_loops) > 1 else None

    @property
    def x_label(self) -> str:
        """Create x label for live plotting.

        Returns:
            str: X label.
        """
        if len(self.all_loops) == 0:
            return "Sequence idx"

        return self.label(loop=self.all_loops[0])

    def label(self, loop: Loop) -> str:
        """Return plot label from loop object.

        Args:
            loop (Loop): Loop class.

        Returns:
            str: Plot label.
        """
        instrument_name = loop.alias
        return f"{instrument_name}: {loop.parameter.value} "
