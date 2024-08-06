from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

from qililab.platform.components import Bus
from qililab.waveforms import Arbitrary as ArbitraryWave


@dataclass
class AnnealingProgram:
    """Class for an Annealing Program. The program should have the format

    [
        {"qubit_0": {"sigma_x" : 0, "sigma_y" : 1, "sigma_z" : 2},
         "coupler_1_0 : {...},
        },      # time=0ns
        {...},  # time=1ns
    .
    .
    .
    ]
    """

    platform: Any
    anneal_program: list[dict[str, dict[str, float]]]

    def transpile(self, transpiler: Callable):
        """First implementation of a transpiler, pretty basic but good as a first step. Transpiles from ising coefficients to fluxes

        Args:
            transpiler (Callable): Transpiler to use. The transpiler should take 2 values as arguments (delta, epsilon)
            and return 2 values (phix, phiz)
        """

        # iterate over each anneal step and transpile ising to fluxes
        for anneal_step in self.anneal_program:
            for circuit_element in anneal_step:
                phix, phiz = transpiler(
                    delta=anneal_step[circuit_element]["sigma_x"], epsilon=anneal_step[circuit_element]["sigma_z"]
                )
                anneal_step[circuit_element]["phix"] = phix
                anneal_step[circuit_element]["phiz"] = phiz

    def get_waveforms(self) -> dict[str, tuple[Bus, ArbitraryWave]]:
        """Returns a dictionary containing (bus, waveform) for each flux control from the transpiled fluxes. `AnnealingProgram.transpile` should be run first. The waveform is an arbitrary waveform obtained from the transpiled fluxes.

        Returns:
            dict[str,tuple[Bus,ArbitraryWave]]: Dictionary containing (bus, waveform) for each flux control (i.e. phix or phiz).
        """
        # parse names from algorithm notation (e.g. qubit_0) to runcard notation (e.g. q0)
        element_name_map = {"qubit": "q", "coupler": "c"}
        circuit_element_map = {
            (element, flux): f"{flux}_{element_name_map[element.split('_', 1)[0]]}{element.split('_', 1)[1]}"
            for element in self.anneal_program[0].keys()
            for flux in self.anneal_program[0][element].keys()
            if "phi" in flux
        }  # {(element, flux): flux_line}

        # Initialize dictionary with flux_lines pointing to (corresponding bus, waveform)
        anneal_waveforms = {  # type: ignore[var-annotated]
            flux_line: (self.platform.get_element(flux_line), []) for flux_line in circuit_element_map.values()
        }
        # unravel each point of the anneal program to get timewise arrays of waveforms
        for anneal_step in self.anneal_program:
            for circuit_element, flux in circuit_element_map.keys():
                anneal_waveforms[circuit_element_map[circuit_element, flux]][1].append(
                    anneal_step[circuit_element][flux]
                )

        return {key: (value[0], ArbitraryWave(np.array(value[1]))) for key, value in anneal_waveforms.items()}
