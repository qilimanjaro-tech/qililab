"""Run circuit experiment"""
import os
from pathlib import Path

import h5py
import matplotlib.pyplot as plt
import numpy as np
from qibo.gates import M
from qibo.models.circuit import Circuit
from qiboconnection.api import API

from qililab import build_platform
from qililab.config import logger
from qililab.experiment import Experiment
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.typings import ExperimentOptions, ExperimentSettings, Parameter
from qililab.typings.loop import LoopOptions
from qililab.utils import Loop

logger.setLevel(30)

os.environ["RUNCARDS"] = "./runcards"
os.environ["DATA"] = "/home/jupytershared/data"


def run_and_plot(
    title: str,
    frequency_start: float,
    frequency_stop: float,
    frequency_num: int,
    current_start: float | None,
    current_stop: float | None,
    current_num: int | None,
    attenuation_fixed: float,
    current_fixed: float,
):
    """Load the platform 'flux_spectroscopy' from the DB."""
    platform = build_platform(name="sauron")
    platform.connect_and_set_initial_setup(automatic_turn_on_instruments=True, device_id=15)

    # Define Circuit to execute
    circuit = Circuit(1)
    circuit.add(M(0))

    frequency_loop_options = LoopOptions(start=frequency_start, stop=frequency_stop, num=frequency_num)
    frequency_loop = Loop(alias="rs_1", parameter=Parameter.LO_FREQUENCY, options=frequency_loop_options)

    if current_start is not None:
        current_loop_options = LoopOptions(start=current_start, stop=current_stop, num=current_num, channel_id=0)
        current_loop = Loop(alias="S4g", parameter=Parameter.CURRENT, options=current_loop_options, loop=frequency_loop)

    if current_start is not None:
        loop = current_loop
    else:
        loop = frequency_loop

    # Instantiate Experiment class
    experiment_options = ExperimentOptions(
        loops=[loop],
        name=f"{title}",
        # connection=connection,
        # device_id=15,
        settings=ExperimentSettings(repetition_duration=10000, hardware_average=10000),
    )

    flux_spectro = Experiment(
        platform=platform, circuits=[circuit], options=experiment_options
    )  # if you don't want to define any settings just remove settings=settings.

    flux_spectro.set_parameter(alias="M", parameter=Parameter.DURATION, value=8000)

    gain = 1.0
    flux_spectro.set_parameter(alias="QRM", parameter=Parameter.GAIN_I, value=gain, channel_id=0)
    flux_spectro.set_parameter(alias="QRM", parameter=Parameter.GAIN_Q, value=gain, channel_id=0)

    if_freq = 2e7
    flux_spectro.set_parameter(alias="QRM", parameter=Parameter.IF, value=if_freq, channel_id=0)

    store_scope = False
    flux_spectro.set_parameter(alias="QRM", parameter=Parameter.SCOPE_STORE_ENABLED, value=store_scope, channel_id=0)

    flux_spectro.set_parameter(alias="attenuator", parameter=Parameter.ATTENUATION, value=attenuation_fixed)

    flux_spectro.set_parameter(alias="S4g", parameter=Parameter.SPAN, value="range_max_bi", channel_id=0)
    flux_spectro.set_parameter(alias="S4g", parameter=Parameter.CURRENT, value=current_fixed, channel_id=0)

    results = flux_spectro.execute()

    acquisitions = results.acquisitions()
    i_acq = acquisitions["i"]
    q_acq = acquisitions["q"]
    frequency = np.linspace(start=frequency_loop.start, stop=frequency_loop.stop, num=frequency_loop.num) * 1e-9

    if current_start is not None:
        current = np.linspace(start=current_loop.start, stop=current_loop.stop, num=current_loop.num)

        i_np = np.array(i_acq)
        q_np = np.array(q_acq)
        I_signal = i_np.reshape(([current_loop.num, frequency_loop.num]))
        Q_signal = q_np.reshape(([current_loop.num, frequency_loop.num]))
        S21 = 20 * np.log10(I_signal**2 + Q_signal**2)

        plt.figure(figsize=(9, 7))
        plt.pcolor(frequency, current, S21, cmap="Greens")
        plt.colorbar(label="|S21|")
        plt.xlabel("Frequency [GHz]")
        plt.ylabel("Current [A]")
        plt.title(f"{title}")
    else:
        S21 = 20 * np.log10(i_np**2 + q_np**2)
        plt.figure(figsize=(9, 7))
        plt.plot(frequency, S21)
        plt.xlabel("Frequency [GHz]")
        plt.ylabel("|S21|")
        plt.title(f"{title}")
