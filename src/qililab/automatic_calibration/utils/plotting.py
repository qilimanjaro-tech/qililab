import numpy as np
import matplotlib.pyplot as plt


def plot_iq(xdata, results: np.ndarray, title_label: str, xlabel: str):
    fig, axes = plt.subplots(1, 2, figsize=(13, 7))
    axes[0].plot(xdata, results[0], "--o", color="blue")
    axes[1].plot(xdata, results[1], "--o", color="blue")
    axes[0].set_title("I")
    axes[1].set_title("Q")
    axes[0].set_xlabel(xlabel)
    axes[1].set_xlabel(xlabel)
    axes[0].set_ylabel("Voltage [a.u.]")
    axes[1].set_ylabel("Voltage [a.u.]")
    fig.suptitle(title_label)
    return fig, axes