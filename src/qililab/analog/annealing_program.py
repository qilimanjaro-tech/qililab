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

from typing import Any, Callable

import numpy as np

from qililab.platform.components import Bus
from qililab.qprogram import CrosstalkMatrix
from qililab.waveforms import Arbitrary as ArbitraryWave


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

    def __init__(self, platform: Any, annealing_program: list[dict[str, dict[str, float]]]):
        """Init method"""
        self._platform = platform
        self._annealing_program = annealing_program
        self.annealing_program = annealing_program  # TODO: implement as frozenDataclass

    def transpile(self, transpiler: Callable):
        """First implementation of a transpiler, pretty basic but good as a first step. Transpiles from ising coefficients to fluxes

        Args:
            transpiler (Callable): Transpiler to use. The transpiler should take 2 values as arguments (delta, epsilon)
            and return 2 values (phix, phiz)
        """

        # iterate over each anneal step and transpile ising to fluxes
        for annealing_step in self._annealing_program:
            for chip_element in annealing_step:
                phix, phiz = transpiler(
                    delta=annealing_step[chip_element]["sigma_x"], epsilon=annealing_step[chip_element]["sigma_z"]
                )
                annealing_step[chip_element]["phix"] = phix
                annealing_step[chip_element]["phiz"] = phiz

    def get_waveforms(self, xtalk_matrix: CrosstalkMatrix | None = None) -> dict[str, tuple[Bus, ArbitraryWave]]:
        """Returns a dictionary containing (bus, waveform) for each flux control from the transpiled fluxes. `AnnealingProgram.transpile` should be run first. The waveform is an arbitrary waveform obtained from the transpiled fluxes.

        Returns:
            dict[str,tuple[Bus,ArbitraryWave]]: Dictionary containing (bus, waveform) for each flux control (i.e. phix or phiz).
        """
        # TODO: clean and optimize
        # parse names from algorithm notation (e.g. qubit_0) to runcard notation (e.g. q0)
        element_name_map = {"qubit": "q", "coupler": "c"}
        chip_element_map = {
            (element, flux): f"{flux}_{element_name_map[element.split('_', 1)[0]]}{element.split('_', 1)[1]}"
            for element in self._annealing_program[0].keys()
            for flux in self._annealing_program[0][element].keys()
            if "phi" in flux
        }  # {(chip element(qubit/coupler), flux): flux_line}
        chip_element_map_inverse = {v: k for k, v in chip_element_map.items()}

        # Initialize dictionary with flux_lines pointing to (corresponding bus, waveform)
        annealing_waveforms = {  # type: ignore[var-annotated]
            flux_line: (self._platform.get_element(flux_line), []) for flux_line in chip_element_map.values()
        }
        # unravel each point of the anneal program to get timewise arrays of waveforms
        for annealing_step in self._annealing_program:
            bus_flux_dict = {
                bus: annealing_step[chip_element][flux] for (chip_element, flux), bus in chip_element_map.items()
            }
            corrected_flux = xtalk_matrix @ bus_flux_dict
            for bus, value in corrected_flux.items():
                annealing_waveforms[chip_element_map_inverse[bus][1]][1].append(value)

            # for chip_element, flux in chip_element_map.keys():

            #     flux = annealing_step[chip_element][flux]
            #     bus_flux_dict =

            #     annealing_waveforms[chip_element_map[chip_element, flux]][1].append(
            #         annealing_step[chip_element][flux]
            #     )

        return {key: (value[0], ArbitraryWave(np.array(value[1]))) for key, value in annealing_waveforms.items()}
