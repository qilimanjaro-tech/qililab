"""LivePlot class."""
from dataclasses import InitVar, dataclass, field
from itertools import count
from typing import Iterator, List

import numpy as np
from qiboconnection.api import API

from qililab.constants import DEFAULT_PLOT_Y_LABEL
from qililab.typings.enums import LivePlotTypes
from qililab.utils.loop import Loop
from qililab.utils.util_loops import find_minimum_inner_range_from_loops, find_minimum_outer_range_from_loops


@dataclass
class LivePlot:
    """Plot class."""

    connection: API
    num_schedules: int
    loops: List[Loop] | None = None
    plot_id: int = field(init=False)
    x_iterator_ranges: Iterator = field(init=False)
    y_iterator_ranges: Iterator = field(init=False)
    plot_y_label: str | None = None
    title: InitVar[str] = ""

    def __post_init__(self, title: str):
        """Generate iterators that iterate over loop ranges."""
        self.x_iterator_ranges, self.y_iterator_ranges = self._build_plot_ranges_from_loop_ranges(
            num_schedules=self.num_schedules
        )
        self.plot_id = self.create_live_plot(title=title)

    def _build_plot_ranges_from_loop_ranges(self, num_schedules: int) -> List[Iterator]:
        """build plot ranges from loop ranges"""
        return (
            (self._build_empty_iterator(), self._build_empty_iterator())
            if self.loops is None
            else self._build_plot_ranges_from_defined_loop_ranges(num_schedules=num_schedules)
        )

    def _build_empty_iterator(self):
        """build empty iterator"""
        return count()

    def _build_plot_ranges_from_defined_loop_ranges(self, num_schedules: int):
        """build plot ranges from defined loop ranges"""
        x_loop_range = np.tile(find_minimum_outer_range_from_loops(loops=self.loops), num_schedules)
        y_loop_range = np.tile(find_minimum_inner_range_from_loops(loops=self.loops), num_schedules)

        if y_loop_range is None or len(y_loop_range) <= 0:
            return (iter(x_loop_range), self._build_empty_iterator())

        ranges_meshgrid = np.meshgrid(x_loop_range, y_loop_range)
        return iter(ranges_meshgrid[0].ravel()), iter(ranges_meshgrid[1].ravel())

    def create_live_plot(self, title: str) -> int:
        """Create live plot

        Args:
            title (str): Title of the plot.
            x_label (str): Label of the x axis.
            y_label (str): Label of the y axis.
        """
        return self.connection.create_liveplot(
            title=title,
            x_label=self.x_label,
            y_label=self.y_label,
            z_label=self.z_label,
            plot_type=self.plot_type.value,
            x_axis=self.x_axis,
            y_axis=self.y_axis,
        )

    def send_points(self, value: float):
        """Send plot points.

        Args:
            value (float): value to send to the plot
        """
        if self.plot_type in [LivePlotTypes.SCATTER, LivePlotTypes.LINES]:
            x_value = next(self.x_iterator_ranges)
            self.connection.send_plot_points(plot_id=self.plot_id, x=float(x_value), y=value)
            return
        if self.plot_type == LivePlotTypes.HEATMAP:
            x_value = next(self.x_iterator_ranges)
            y_value = next(self.y_iterator_ranges)
            self.connection.send_plot_points(
                plot_id=self.plot_id,
                x=float(x_value),
                y=float(y_value),
                z=value,
            )
            return
        raise ValueError(
            f"PlotType {self.plot_type.value} not supported. Plot valid types are: "
            + f"{[plot_type.value for plot_type in LivePlotTypes]}"
        )

    @property
    def total_inner_loops(self):
        """return total inner loops"""
        return 0 if self.loops is None else max(loop.num_loops for loop in self.loops)

    @property
    def plot_type(self) -> LivePlotTypes:
        """Return plot type.

        Returns:
            LivePlotTypes: Type of the LivePlot
        """
        if self.loops is None or self.total_inner_loops <= 1:
            return LivePlotTypes.SCATTER
        return LivePlotTypes.HEATMAP

    @property
    def x_axis(self):
        """Loop 'x_axis' property.

        Returns:
            List[int]: Values of the x axis.
        """
        if self.loops is None:
            return None
        return find_minimum_outer_range_from_loops(loops=self.loops)

    @property
    def y_axis(self):
        """Loop 'y_axis' property.

        Returns:
            List[int]: Values of the y axis.
        """
        if self.loops is None:
            return None
        if self.loops[0].inner_loop_range is None:
            return None
        return find_minimum_inner_range_from_loops(loops=self.loops)

    @property
    def y_label(self):
        """Create y label for live plotting.

        Returns:
            str: Y label.
        """
        if self.plot_y_label is not None:
            return self.plot_y_label
        if self._has_multiple_loops():
            for loop in self.loops:
                if loop.inner_loop_range is not None:
                    return self.label(loop=loop.loops[-2])

        return DEFAULT_PLOT_Y_LABEL

    def _has_multiple_loops(self):
        """check if loops variable has multiple loops"""
        return self.loops is not None and self.total_inner_loops > 1

    @property
    def z_label(self) -> str | None:
        """Create z label for live plotting.

        Returns:
            str: Z label.
        """
        return "Amplitude" if self._has_multiple_loops() else None

    @property
    def x_label(self) -> str:
        """Create x label for live plotting.

        Returns:
            str: X label.
        """
        if self.loops is None:
            return "Sequence idx"

        minimum_outer_loop_range_length = len(self.loops[0].outer_loop_range)
        index = 0
        for loop in self.loops:
            if len(loop.outer_loop_range) < minimum_outer_loop_range_length:
                minimum_outer_loop_range_length = len(loop.outer_loop_range)
                index += 1
        return self.label(loop=self.loops[index].loops[-1])

    def label(self, loop: Loop) -> str:
        """Return plot label from loop object.

        Args:
            loop (Loop): Loop class.

        Returns:
            str: Plot label.
        """
        instrument_name = loop.alias
        return f"{instrument_name}: {loop.parameter.value} "
