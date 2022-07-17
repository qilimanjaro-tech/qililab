"""LivePlot class."""
from dataclasses import InitVar, dataclass, field
from functools import partial
from itertools import count
from typing import Callable, Iterator, List

import numpy as np
from qiboconnection.api import API as Connection

from qililab.config import logger
from qililab.constants import DEFAULT_PLOT_Y_LABEL
from qililab.remote_connection import RemoteAPI
from qililab.typings.enums import LivePlotTypes
from qililab.utils.loop import Loop


@dataclass
class LivePlot:
    """Plot class."""

    remote_api: RemoteAPI
    loop: Loop | None = None
    plot_ids: List[int] = field(default_factory=list)
    x_iterator_ranges: Iterator = field(init=False)
    y_iterator_ranges: Iterator = field(init=False)
    ranges: List[Iterator] = field(init=False)
    plot_y_label: str | None = None
    title: InitVar[str] = ""

    def __post_init__(self, title: str):
        """Generate iterators that iterate over loop ranges."""
        self.x_iterator_ranges, self.y_iterator_ranges = self._build_plot_ranges_from_loop_ranges()
        self.create_live_plot(title=title)

    def _build_plot_ranges_from_loop_ranges(self) -> List[Iterator]:
        """build plot ranges from loop ranges"""
        return (
            (self._build_empty_iterator(), self._build_empty_iterator())
            if self.loop is None
            else self._build_plot_ranges_from_defined_loop_ranges()
        )

    def _build_empty_iterator(self):
        """build empty iterator"""
        return count()

    def _build_plot_ranges_from_defined_loop_ranges(self):
        """build plot ranges from defined loop ranges"""
        x_loop_range, y_loop_range = self.loop.outer_loop_range, self.loop.inner_loop_range

        if y_loop_range is None:
            return (iter(x_loop_range), self._build_empty_iterator())

        ranges_meshgrid = np.meshgrid(x_loop_range, y_loop_range)
        return iter(ranges_meshgrid[0].ravel()), iter(ranges_meshgrid[1].ravel())

    class CheckRemoteApiInitialized:
        """Property used to check if the Remote API has been initialized."""

        def __init__(self, method: Callable):
            self._method = method

        def __get__(self, obj, objtype):
            """Support instance methods."""
            return partial(self.__call__, obj)

        def __call__(self, ref: "LivePlot", *args, **kwargs):
            """
            Args:
                method (Callable): Class method.

            Raises:
                AttributeError: If connection has not been initialized.
            """
            if not hasattr(ref, "remote_api") or ref.remote_api is None:
                logger.debug("Live plotting disabled. Remote API has not been initialized.")
                return
            if ref.remote_api.connection is None:
                logger.debug("Live plotting disabled. Remote Connection has not been initialized.")
                return
            return self._method(ref, *args, **kwargs)

    @CheckRemoteApiInitialized
    def create_live_plot(self, title: str):
        """Create live plot

        Args:
            title (str): Title of the plot.
            x_label (str): Label of the x axis.
            y_label (str): Label of the y axis.
        """
        self.plot_ids.append(
            self.connection().create_liveplot(
                title=title,
                x_label=self.x_label,
                y_label=self.y_label,
                z_label=self.z_label,
                plot_type=self.plot_type.value,
                x_axis=self.x_axis,
                y_axis=self.y_axis,
            )
        )

    @CheckRemoteApiInitialized
    def send_points(self, value: float):
        """Send plot points.

        Args:
            value (float): value to send to the plot
        """
        if self.plot_type == LivePlotTypes.SCATTER or self.plot_type == LivePlotTypes.LINES:
            self.connection().send_plot_points(
                plot_id=self.plot_ids[-1], x=float(next(self.x_iterator_ranges)), y=float(value)
            )
            return
        if self.plot_type == LivePlotTypes.HEATMAP:
            self.connection().send_plot_points(
                plot_id=self.plot_ids[-1],
                x=float(next(self.x_iterator_ranges)),
                y=float(next(self.y_iterator_ranges)),
                z=float(value),
            )
            return
        raise ValueError(
            f"PlotType {self.plot_type.value} not supported. Plot valid types are: {[plot_type.value for plot_type in LivePlotTypes]}"
        )

    @property
    def plot_type(self) -> LivePlotTypes:
        """Return plot type.

        Returns:
            LivePlotTypes: Type of the LivePlot
        """
        return LivePlotTypes.HEATMAP if (self.loop is not None and self.loop.num_loops > 1) else LivePlotTypes.SCATTER

    @property
    def x_axis(self):
        """Loop 'x_axis' property.

        Returns:
            List[int]: Values of the x axis.
        """
        return self.loop.outer_loop_range if self.loop is not None else None

    @property
    def y_axis(self):
        """Loop 'y_axis' property.

        Returns:
            List[int]: Values of the y axis.
        """
        return self.loop.inner_loop_range if self.loop is not None else None

    @property
    def y_label(self):
        """Create y label for live plotting.

        Returns:
            str: Y label.
        """
        if self.plot_y_label is not None:
            return self.plot_y_label
        if self.loop is not None and self.loop.num_loops > 1:
            return self.label(loop=self.loop.loops[-2])

        return DEFAULT_PLOT_Y_LABEL

    @property
    def z_label(self) -> str | None:
        """Create z label for live plotting.

        Returns:
            str: Z label.
        """
        if self.loop is not None and self.loop.num_loops > 1:
            return "Amplitude"

        return None

    @property
    def x_label(self) -> str:
        """Create x label for live plotting.

        Returns:
            str: X label.
        """
        if self.loop is not None:
            return self.label(loop=self.loop.loops[-1])

        return "Sequence idx"

    @CheckRemoteApiInitialized
    def connection(self) -> Connection:
        """Return the Remote API Connection if it is created"""
        return self.remote_api.connection

    def label(self, loop: Loop) -> str:
        """Return plot label from loop object.

        Args:
            loop (Loop): Loop class.

        Returns:
            str: Plot label.
        """
        instrument_name = (
            loop.alias
            if loop.alias is not None
            else f"{loop.instrument.value if loop.instrument is not None else None} "
            + f"{loop.id_ if loop.id_ is not None else None}"
        )
        return f"{instrument_name}: {loop.parameter.value} "
