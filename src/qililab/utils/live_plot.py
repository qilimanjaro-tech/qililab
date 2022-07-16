"""LivePlot class."""
from dataclasses import InitVar, dataclass, field
from functools import partial
from itertools import count
from typing import Callable, Iterator, List

import numpy as np
from qiboconnection.api import API as Connection

from qililab.config import logger
from qililab.remote_connection import RemoteAPI
from qililab.typings.enums import LivePlotTypes
from qililab.utils.loop import Loop


@dataclass
class LivePlot:
    """Plot class."""

    remote_api: RemoteAPI
    loop: Loop | None
    plot_ids: List[int] = field(default_factory=list)
    ranges: List[Iterator] = field(init=False)
    title: InitVar[str] = ""

    def __post_init__(self, title: str):
        """Generate iterators that iterate over loop ranges."""
        if self.loop is not None:
            x_loop = self.loop.loops[-1].range
            y_loop = self.loop.loops[-2].range if self.loop.num_loops > 1 else None
            ranges_meshgrid = np.meshgrid(x_loop, y_loop)  # type: ignore
            self.ranges = [iter(range[0]) for range in ranges_meshgrid]
        else:
            self.ranges = [count()]
        self.create_live_plot(title=title)

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
        # sourcery skip: remove-unnecessary-cast
        """Send plot points.

        Args:
            x_value (float): X value.
            y_value (float): Y value.
        """
        if self.plot_type == LivePlotTypes.SCATTER or self.plot_type == LivePlotTypes.LINES:
            self.connection().send_plot_points(plot_id=self.plot_ids[-1], x=float(next(self.ranges[0])), y=float(value))
            return
        if self.plot_type == LivePlotTypes.HEATMAP:
            self.connection().send_plot_points(
                plot_id=self.plot_ids[-1],
                x=float(next(self.ranges[0])),
                y=float(next(self.ranges[1])),
                z=float(value),
            )
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
        return self.loop.ranges[-1] if self.loop is not None else None

    @property
    def y_axis(self):
        """Loop 'y_axis' property.

        Returns:
            List[int]: Values of the y axis.
        """
        return self.loop.ranges[-2] if (self.loop is not None and self.loop.num_loops > 1) else None

    @property
    def y_label(self):
        """Create y label for live plotting.

        Returns:
            str: Y label.
        """
        if self.loop is not None and self.loop.num_loops > 1:
            return self.label(loop=self.loop.loops[-2])

        return "Sequence idx"

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
