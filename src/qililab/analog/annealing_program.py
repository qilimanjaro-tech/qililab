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

from typing import Callable

import numpy as np

from qililab.qprogram import CrosstalkMatrix, FluxVector
from qililab.settings.analog import FluxControlTopology
from qililab.waveforms import Arbitrary


class AnnealingProgram:
    """Class for an Annealing Program. The program should have the format

    .. code-block:: python

        [
            {"qubit_0": {"sigma_x" : 0, "sigma_y" : 1, "sigma_z" : 2},
            "coupler_1_0 : {...},
            },      # time=0ns
            {...},  # time=1ns
        .
        .
        .
        ]


    Args:
        platform (Any): platform
        annealing_program (list[dict[str, dict[str, float]]]): dictionary with the annealing program with the above structure.
    """

    def __init__(
        self,
        flux_to_bus_topology: list[FluxControlTopology],
        annealing_program: list[dict[str, dict[str, float]]],
    ):
        """Init method"""
        self._flux_to_bus_topology = flux_to_bus_topology
        self._annealing_program = annealing_program
        self._transpiled_program = []  # type: list # [anneal_step[chip_element_flux_line,value]]

    def transpile(self, transpiler: Callable):
        """First implementation of a transpiler, pretty basic but good as a first step. Transpiles from ising coefficients to fluxes

        Args:
            transpiler (Callable): Transpiler to use. The transpiler should take 2 values as arguments (delta, epsilon)
            and return 2 values (phix, phiz)
        """

        # iterate over each anneal step and transpile ising to fluxes
        for annealing_step in self._annealing_program:
            transpiled_step = {}
            for chip_element in annealing_step:
                phix, phiz = transpiler(
                    delta=annealing_step[chip_element]["sigma_x"], epsilon=annealing_step[chip_element]["sigma_z"]
                )
                transpiled_step[f"phix_{self._chip_element_to_short(chip_element)}"] = phix
                transpiled_step[f"phiz_{self._chip_element_to_short(chip_element)}"] = phiz

            self._transpiled_program.append(transpiled_step.copy())

    def _chip_element_to_short(self, chip_element: str) -> str:
        """Parse names from algorithm notation (e.g. qubit_0) to runcard notation (e.g. q0)

        Args:
            chip_element[str]: name of the chip element
        Returns
            str: shorthand notation
        """
        split_element = chip_element.split("_")
        return (
            f"{chip_element[0]}{split_element[1]}"
            if chip_element[0] == "q"
            else f"{chip_element[0]}{split_element[1]}_{split_element[2]}"
        )

    def get_waveforms(
        self, crosstalk_matrix: CrosstalkMatrix | None = None, minimum_clock_time: int = 1
    ) -> dict[str, Arbitrary]:
        """Returns a dictionary containing (bus, waveform) for each flux control from the transpiled fluxes. `AnnealingProgram.transpile` should be run first. The waveform is an arbitrary waveform obtained from the transpiled fluxes.

        Args:
            crosstalk_matrix[CrosstalkMatrix]: crosstalk matrix to correct the flux vectors with. This is usually the inverse of the crosstalk matrix
            in the Calibration file obtained from experiments.
            minimum_clock_time [int]: minimum unit of clock time for the awg (in ns). Waveforms should be multiples of this. Defaults to 1, equivalent to 1ns resolution.
        Returns:
            dict[str, Arbitrary]: Dictionary containing the waveform to be sent to each bus, with xtalk corrected
        """

        # Initialize maps for bus to flux and flux to bus translation
        bus_to_flux_map = {}
        for flux_bus in self._flux_to_bus_topology:
            if flux_bus.flux in self._transpiled_program[0]:
                if flux_bus.bus in bus_to_flux_map:
                    raise ValueError(
                        f"More than one flux pointing at bus {flux_bus.bus} in the runcard flux to bus topology"
                    )
                bus_to_flux_map[flux_bus.bus] = flux_bus.flux
        flux_to_bus_map = {v: k for k, v in bus_to_flux_map.items()}

        # add padding to waveforms if duration is not multiple of minimum clock time
        padded_ns = 0
        if len(self._transpiled_program) % minimum_clock_time != 0:
            padded_ns = (
                minimum_clock_time - len(self._transpiled_program) % minimum_clock_time
                if len(self._transpiled_program) % minimum_clock_time != 0
                else 0
            )

        # Initialize annealing waveforms
        annealing_waveforms = {bus: padded_ns * [0.0] for bus in bus_to_flux_map}  # type: ignore[var-annotated]

        # unravel each point of the anneal program to get timewise arrays of waveforms
        for annealing_step in self._transpiled_program:
            bus_flux_dict = FluxVector.from_dict(
                {flux_to_bus_map[flux_line]: value for flux_line, value in annealing_step.items()}
            )
            flux_dict = (
                bus_flux_dict.set_crosstalk(crosstalk_matrix)
                if crosstalk_matrix is not None
                else bus_flux_dict.flux_vector
            )
            for bus, value in flux_dict.items():
                annealing_waveforms[bus].append(value)  # type: ignore

        return {key: Arbitrary(np.array(value)) for key, value in annealing_waveforms.items()}
