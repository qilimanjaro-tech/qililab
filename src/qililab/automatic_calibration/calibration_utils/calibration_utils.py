"""
Useful functions for calibration experiments and data analysis.
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
    labels = {node: node.node_id for node in calibration_graph.nodes}
    nx.draw_planar(calibration_graph, labels=labels, with_labels=True)
    plt.savefig(graph_figure_path, format="PNG")
    graph_figure = mpimg.imread(graph_figure_path)
    plt.imshow(graph_figure)
    plt.show()
    # This closes the figure containing the graph drawing. Every time we call plt.show() in the future, 
    # for example to show the plot given by an analysis function to the user, all open figures will be shown,
    # including this one showing the graph drawing, which we don't want.
    plt.close()

def get_timestamp() -> int:
    """Generate a UNIX timestamp.

    Returns:
        int: UNIX timestamp of the time when the function is called.
    """
    now = datetime.now()
    return datetime.timestamp(now)


def is_timeout_expired(timestamp, timeout):
    """
    Check if the time passed since the timestamp is greater than the timeout duration.

    Args:
        timestamp (int): Timestamp from which the time should be checked, described in UNIX timestamp format.
        timeout (int): The timeout duration in seconds.

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


# TODO: docstrings. I took this from LabScripts/QuantumPainHackathon/calibration/calibration.py and I don't know what
# it does yet, it's only here because it's used in analysis functions.
def plot_iq(xdata, i, q, title_label, xlabel):
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


# TODO: docstrings. I took this from LabScripts/QuantumPainHackathon/calibration/calibration.py and I don't know what
# it does yet, it's only here because it's used in analysis functions.
def plot_fit(xdata, popt, ax, fitted_pi_pulse_amplitude):
    # Create label text

    def sinus(x, a, b, c, d):
        return a * np.sin(2 * np.pi * b * np.array(x) - c) + d

    # func = sinus()
    # args = list(inspect.signature(func).parameters.keys())[1:]
    # text = "".join(f"{arg}: {value:.5f}\n" for arg, value in zip(args, popt))

    label_fit = f"FIT $A_\pi$ = {fitted_pi_pulse_amplitude:.3f}"
    ax.plot(xdata, sinus(xdata, *popt), "--", label=label_fit, color="red")
    ax.legend()

def get_most_recent_folder(directory: str):
    subfolders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
    
    if not subfolders:
        return None
    
    # Convert folder names to timestamps and find the most recent one
    most_recent_folder = max(subfolders, key=lambda x: float(x))
    
    return os.path.join(directory, most_recent_folder)