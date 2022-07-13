"""LivePlot class."""
from dataclasses import dataclass, field
from itertools import count
from typing import Iterator, List

import numpy as np
from qiboconnection.api import API as Connection

from qililab.remote_connection import RemoteAPI
from qililab.utils.loop import Loop


@dataclass
class LivePlot:
    """Plot class."""

    remote_api: RemoteAPI | None
    loop: Loop | None
    plot_ids: List[int] = field(default_factory=list)
    ranges: List[Iterator] = field(init=False)

    def __post_init__(self):
        """Generate iterators that iterate over loop ranges."""
        if self.loop is not None:
            x_loop = self.loop.loops[-1].range
            y_loop = self.loop.loops[-2].range if self.loop.num_loops > 1 else None
            ranges_meshgrid = np.meshgrid(x_loop, y_loop)  # type: ignore
            self.ranges = [iter(range[0]) for range in ranges_meshgrid]
        else:
            self.ranges = [count()]

    def create_live_plot(self, title: str):
        """Create live plot

        Args:
            title (str): Title of the plot.
            x_label (str): Label of the x axis.
            y_label (str): Label of the y axis.
            plot_type (str, optional): Plot type. Options are "LINES", "SCATTER3D" or "HEATMAP". Defaults to "LINES".
        """
        if self.connection is not None:
            self.plot_ids.append(
                self.connection.create_liveplot(
                    title=title,
                    x_label=self.x_label,
                    y_label=self.y_label,
                    z_label=self.z_label,
                    plot_type=self.plot_type,
                    x_axis=self.x_axis,
                    y_axis=self.y_axis,
                )
            )

    def send_points(self, value: float):
        # sourcery skip: remove-unnecessary-cast
        """Send plot points.

        Args:
            x_value (float): X value.
            y_value (float): Y value.
        """
        if self.connection is not None:
            if self.plot_type == "SCATTER":
                self.connection.send_plot_points(
                    plot_id=self.plot_ids[-1], x=float(next(self.ranges[0])), y=float(value)
                )
            elif self.plot_type == "HEATMAP":
                self.connection.send_plot_points(
                    plot_id=self.plot_ids[-1],
                    x=float(next(self.ranges[0])),
                    y=float(next(self.ranges[1])),
                    z=float(value),
                )

    @property
    def plot_type(self) -> str:
        """Return plot type.

        Returns:
            str: HEATMAP if 3D else SCATTER.
        """
        return "HEATMAP" if (self.loop is not None and self.loop.num_loops > 1) else "SCATTER"

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

    @property
    def connection(self) -> Connection | None:
        """Return the Remote API connection if it is created"""
        return None if self.remote_api is None else self.remote_api.connection

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
