"""
Module with useful functions for calibration experiments and data analysis.
"""

import random
from datetime import datetime, timedelta
import os
import networkx as nx

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import yaml

def visualize_calibration_graph(calibration_graph: nx.DiGraph, graph_figure_path: str):
    """
    Visualizes a calibration graph using networkx and saves the visualization as an image.

    This function takes a calibration graph represented as a directed graph and generates a planar visualization
    with node labels. The visualization is then saved as an image file at the specified path. The saved image
    is also displayed to the user.

    Args:
        calibration_graph (nx.DiGraph): The calibration graph to visualize.
        graph_figure_path (str): The file path to save the visualization image.

    Returns:
        None
    """
    labels = {node: node.node_id for node in calibration_graph.nodes}
    nx.draw_planar(calibration_graph, labels=labels, with_labels=True)
    plt.savefig(graph_figure_path, format="PNG")
    graph_figure = mpimg.imread(graph_figure_path)
    plt.imshow(graph_figure)
    plt.show()
    plt.close()

def get_timestamp() -> int:
    """Generate a UNIX timestamp.

    Returns:
        int: UNIX timestamp of the time when the function is called.
    """
    now = datetime.now()
    return datetime.timestamp(now)


def is_timeout_expired(timestamp: float, timeout: float):
    """
    Check if the time passed since the timestamp is greater than the timeout duration.

    Args:
        timestamp (float): Timestamp from which the time should be checked, described in UNIX timestamp format.
        timeout (float): The timeout duration in seconds.

    Returns:
        bool: True if the timeout has expired, False otherwise.
    """
    # Convert the timestamp and timeout to datetime objects
    timestamp_dt = datetime.fromtimestamp(timestamp)
    timeout_duration = timedelta(seconds=timeout)

    # Get the current time
    current_time = datetime.now()

    # Calculate the time that should have passed (timestamp + timeout duration)
    timeout_time = timestamp_dt + timeout_duration

    # Check if the current time is greater than the timeout time
    return current_time > timeout_time


def get_random_values(array: list(), number_of_values: int):
    """
    Returns random values from an array.

    Args:
        array (list(float)): The array from which the random values are retrieved.
        number_of_values (int): The number of random values to be retrieved.

    Raises:
        ValueError: There's fewer elements in the array than the number of values requested to be retrieved.

    Returns:
        list(float): A list of random values from the array.
    """
    if len(array) < number_of_values:
        raise ValueError("Array must contain at least num_of_values elements.")
    return random.sample(sorted(array), number_of_values)


def get_raw_data(datapath):
    """
    Retrieves raw data from a YAML file.

    Args:
        datapath (str): Path to the YAML file.

    Returns:
        dict: Raw data dictionary.
    """
    with open(datapath, "r") as file:
        data_raw = yaml.safe_load(file)
    return data_raw


def get_iq_from_raw(data_raw, index=0):
    """
    Extracts I and Q data from the raw data dictionary.

    Args:
        data_raw (dict): Raw data dictionary.

    Returns:
        tuple: Tuple containing the I and Q arrays.
    """
    i = np.array([item["qblox_raw_results"][index]["bins"]["integration"]["path0"] for item in data_raw["results"]])
    q = np.array([item["qblox_raw_results"][index]["bins"]["integration"]["path1"] for item in data_raw["results"]])
    return i, q


def plot_iq(xdata, i, q, title_label, xlabel):
    """
    Plot the I and Q components of data against the specified x values.

    This function creates a side-by-side plot with two subplots to visualize the I (in-phase) and Q (quadrature)
    components of data as functions of the specified x values. The I and Q components are plotted separately,
    with the given xdata values.

    Args:
        xdata (array-like): The x values for which the I and Q components are plotted.
        i (array-like): The in-phase (I) component values to be plotted.
        q (array-like): The quadrature (Q) component values to be plotted.
        title_label (str): The title for the entire plot.
        xlabel (str): The label for the x-axis.

    Returns:
        tuple: A tuple containing the figure and axes objects of the created plot.

    Note: 
        This function was taken from without any modifications LabScripts/QuantumPainHackathon/calibration/calibration.py
        
    Example:
        
        .. code-block:: python3
        
            xdata = [1, 2, 3, 4, 5]
            i = [0.5, 0.8, 0.7, 1.0, 0.9]
            q = [0.3, 0.6, 0.8, 0.7, 0.5]
            title = "I-Q Components"
            x_label = "Frequency [Hz]"
            fig, axes = plot_iq(xdata, i, q, title, x_label)
            plt.show()
    """
    # Plot data
    fig, axes = plt.subplots(1, 2, figsize=(13, 7))
    # axes.set_title(options.name)
    # axes.set_xlabel(f"{loop.alias}: {loop.parameter.value}")
    # axes.set_ylabel("|S21| [dB]")  # TODO: Change label for 2D plots
    # axes.scatter(xdata, post_processed_results, color="blue")
    axes[0].plot(xdata, i, "--o", color="blue")
    axes[1].plot(xdata, q, "--o", color="blue")
    axes[0].set_title("I")
    axes[1].set_title("Q")
    axes[0].set_xlabel(xlabel)
    axes[1].set_xlabel(xlabel)
    axes[0].set_ylabel("Voltage [a.u.]")
    axes[1].set_ylabel("Voltage [a.u.]")
    fig.suptitle(title_label)
    return fig, axes


def plot_fit(xdata, popt, ax, label):
    """
    Plot the fitted sinusoidal curve on a given axis.

    This function takes the xdata, optimized parameters (popt), and the axis (ax) and plots a sinusoidal curve
    based on the fitted parameters. It also adds a legend to the plot indicating the fitted pi-pulse amplitude.

    Args:
        xdata (array-like): The x values for the data points.
        popt (array-like): Optimized parameters of the fitted sinusoidal function.
        ax (matplotlib.axes._axes.Axes): The axis object where the plot will be created.
        fitted_pi_pulse_amplitude (float): The amplitude of the fitted pi-pulse.

    Returns:
        None

    Note: 
        This function was taken from without any modifications LabScripts/QuantumPainHackathon/calibration/calibration.py
    
    Todo:
        * Add fitting model as argument instead of hardcoding it. Now the function only works with sinus as a model.
    """

    #TODO: this function should be able to fit to any model: add the model as an argument, instead of hardcoding it here.
    def sinus(x, a, b, c, d):
        return a * np.sin(2 * np.pi * b * np.array(x) - c) + d

    # func = sinus()
    # args = list(inspect.signature(func).parameters.keys())[1:]
    # text = "".join(f"{arg}: {value:.5f}\n" for arg, value in zip(args, popt))

    label_fit = f"FIT $A_\pi$ = {label:.3f}"
    ax.plot(xdata, sinus(xdata, *popt), "--", label=label_fit, color="red")
    ax.legend()

# TODO: replace with standard format
def get_most_recent_folder(directory: str):
    subfolders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
    
    if not subfolders:
        return None
    
    # Convert folder names to timestamps and find the most recent one
    most_recent_folder = max(subfolders, key=lambda x: float(x))
    
    return os.path.join(directory, most_recent_folder)