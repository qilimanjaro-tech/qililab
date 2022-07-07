"""LivePlot class."""
from dataclasses import dataclass, field
from typing import List

from qiboconnection.api import API


@dataclass
class LivePlot:
    """Plot class."""

    connection: API | None
    plot_ids: List[int] = field(default_factory=list)

    def create_live_plot(self, title: str, x_label: str, y_label: str, plot_type: str = "SCATTER3D"):
        """Create live plot

        Args:
            title (str): Title of the plot.
            x_label (str): Label of the x axis.
            y_label (str): Label of the y axis.
            plot_type (str, optional): Plot type. Options are "LINES", "SCATTER3D" or "HEATMAP". Defaults to "LINES".
        """
        if self.connection is not None:
            self.plot_ids.append(
                self.connection.create_liveplot(title=title, x_label=x_label, y_label=y_label, plot_type=plot_type)
            )

    def send_points(self, x_value: float, y_value: float):
        # sourcery skip: remove-unnecessary-cast
        """Send plot points.

        Args:
            x_value (float): X value.
            y_value (float): Y value.
        """
        if self.connection is not None and self.plot_ids:
            self.connection.send_plot_points(plot_id=self.plot_ids[-1], x=float(x_value), y=float(y_value))
