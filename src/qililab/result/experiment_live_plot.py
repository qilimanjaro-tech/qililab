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
# mypy: disable-error-code="attr-defined"
import os
import warnings
from dataclasses import dataclass

import numpy as np
import plotly.graph_objects as go
from dash import Dash, Input, Output, callback, dcc, html
from IPython.display import display


@dataclass
class DimensionInfo:
    """Dataclass to store information of a Variable"""

    labels: list[str]
    values: list[np.ndarray]


class ExperimentLivePlot:
    """Provides methods to access the experiment results stored in an HDF5 file."""

    LIVE_PLOT_NAME = "live_plot.png"

    def __init__(self, path: str, slurm_execution: bool = True, port_number: int | None = None):
        """Initializes the ExperimentResults instance.

        Args:
            path (str): The file path to the HDF5 results file.
            slurm_execution (bool): Flag that defines if the liveplot will be held through Dash or a notebook cell. Defaults to True.
            port_number (int|None): Optional parameter for when slurm_execution is True. It defines the port number of the Dash server. Defaults to None.
        """
        self.path = path
        self._slurm_execution = slurm_execution
        self._port_number = port_number

        self.live_plot_dict: dict[tuple[str, str], int] = {}

        self._live_plot_fig: go.Figure | go.FigureWidget
        self._dash_app: Dash

    def live_plot_figures(self, dims_dict: dict[tuple[str, str], list]):
        """Generates the figures for live plotting the S21 parameter from the experiment results.

        Args:
            qprogram (int | str, optional): The index or name of the quantum program. Defaults to 0.
            measurement (int | str, optional): The index or name of the measurement. Defaults to 0.

        Raises:
            NotImplementedError: If the data has more than 2 dimensions.
        """

        if self._slurm_execution:
            self._live_plot_fig = go.Figure()
        else:
            self._live_plot_fig = go.FigureWidget()
        self._live_plot_fig.set_subplots(
            rows=len(dims_dict), cols=1, subplot_titles=[str(key) for key in dims_dict.keys()]
        )
        self._live_plot_fig.update_layout(height=500 * len(dims_dict), width=700, title_text=self.path)

        for n, coordinates in enumerate(dims_dict.keys()):
            self.live_plot_dict[coordinates] = n

        for n, dim in enumerate(dims_dict.values()):
            dims_0 = DimensionInfo(labels=dim[0].label.split(","), values=[values[()] for values in dim[0].values()])  # type: ignore[operator]
            x_labels, x_values = dims_0.labels, dims_0.values
            x_edges = np.linspace(x_values[0].min(), x_values[0].max(), len(x_values[0]) + 1)

            # for n in
            self._live_plot_fig.update_xaxes(title_text=x_labels[0], row=n + 1, col=1)

            n_dimensions = len(dim) - 1
            if n_dimensions == 1:
                self._live_plot_fig.add_scatter(x=x_edges, row=n + 1, col=1)
                self._live_plot_fig.update_yaxes(title_text=r"$|S_{21}|$", row=n + 1, col=1)

            elif n_dimensions == 2:
                dims_1 = DimensionInfo(
                    labels=dim[1].label.split(","),
                    values=[values[()] for values in dim[1].values()],  # type: ignore[operator]
                )
                y_labels, y_values = dims_1.labels, dims_1.values
                y_edges = np.linspace(y_values[0].min(), y_values[0].max(), len(y_values[0]) + 1)

                self._live_plot_fig.add_heatmap(
                    x=x_edges,
                    y=y_edges,
                    row=n + 1,
                    col=1,
                    colorbar_y=1 - (n * (1 / len(dims_dict)) + (1 / (2 * len(dims_dict)))),
                    colorbar_len=1 / len(dims_dict),
                )
                self._live_plot_fig.update_yaxes(title_text=y_labels[0], row=n + 1, col=1)

            else:
                raise NotImplementedError("3D and higher dimension plots are not supported yet.")

        if self._slurm_execution:
            self._dash_app = Dash("Live Plot")
            self._dash_app.layout = html.Div(
                [
                    dcc.Graph(figure=self._live_plot_fig, id="live-plot-graph"),
                    dcc.Interval(id="interval-component", interval=1 * 1000, n_intervals=0),  # in milliseconds
                ]
            )

            @callback(
                Output("live-plot-graph", "figure"),
                Input("interval-component", "n_intervals"),
            )
            def put_more_data_on_figure(n_intervals):
                return self._live_plot_fig

            if not self._port_number:
                self._port_number = 8050
            # TODO: assign with access a host that is not 0.0.0.0 as 127.0.0.1 does not work
            self._dash_app.run(debug=False, host="0.0.0.0", port=self._port_number)  # noqa: S104

        else:
            warnings.filterwarnings("ignore")
            display(self._live_plot_fig)

    def live_plot(self, data: np.ndarray, qprogram_name: str, measurement_name: str):
        """Live plots the S21 parameter from the experiment results.

        Args:
            qprogram (int | str, optional): The index or name of the quantum program. Defaults to 0.
            measurement (int | str, optional): The index or name of the measurement. Defaults to 0.

        Raises:
            NotImplementedError: If the data has more than 2 dimensions.
        """

        def decibels(s21: np.ndarray):
            """Convert result values from s21 into dB"""
            s21[s21 == 0j] = np.nan
            return 20 * np.log10(np.abs(s21))

        n_dimensions = len(data.shape) - 1
        qprogram_num = self.live_plot_dict[qprogram_name, measurement_name]

        # Calculate S21
        s21 = data[..., 0] + 1j * data[..., 1]
        s21 = decibels(s21)

        if n_dimensions == 1:
            self._live_plot_fig.data[qprogram_num].y = s21.T
        elif n_dimensions == 2:
            self._live_plot_fig.data[qprogram_num].z = s21.T

        folder = os.path.dirname(self.path)
        path = os.path.join(folder, ExperimentLivePlot.LIVE_PLOT_NAME)

        self._live_plot_fig.write_image(path)
