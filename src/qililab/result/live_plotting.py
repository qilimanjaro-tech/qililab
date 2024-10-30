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

import time

import h5py
import matplotlib.pyplot as plt
import numpy as np


class LivePlot:
    """
    Live plotter for results saved in an HDF5 file with SWMR mode enabled.

    Args:
        path (str): Path to the HDF5 file.
        refresh_interval (float): Interval in seconds to refresh the plot.
    """

    def __init__(self, path: str, refresh_interval: float = 1.0):
        self.path = path
        self.refresh_interval = refresh_interval
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'b-')  # Initialize an empty line

    def update_plot(self, data):
        """Update the plot with new data."""
        x = np.arange(data.shape[0])
        self.line.set_data(x, data[:, 0])  # Assuming we're plotting the first column only
        self.ax.relim()
        self.ax.autoscale_view()

    def run(self):
        """Continuously reads from the HDF5 file and updates the plot."""
        plt.ion()  # Interactive mode on
        with h5py.File(self.path, "r", swmr=True) as f:
            dataset = f["results"]
            last_size = dataset.shape[0]

            while plt.fignum_exists(self.fig.number):  # Run until the plot window is closed
                current_size = dataset.shape[0]
                if current_size > last_size:  # Check if there's new data
                    data = dataset[:]
                    self.update_plot(data)
                    plt.draw()
                    plt.pause(0.01)  # Small pause to refresh the plot
                    last_size = current_size
                time.sleep(self.refresh_interval)
        
        plt.ioff()  # Turn interactive mode off
