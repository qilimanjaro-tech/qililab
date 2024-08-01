from typing import Callable


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

    def __init__(self, anneal_program: list[dict[str, dict[str, float]]]):
        # implemented only for single qubits so far
        if len(anneal_program[0].keys()) != 1:
            raise ValueError(
                f"The annealing program only supports single qubit anneal so far. Got elements {anneal_program[0].keys()} for the anneal instead"
            )
        self.anneal_program = anneal_program

    def transpile(self, transpiler: Callable):
        """First implementation of a transpiler, pretty basic but good as a first step"""
        # iterate over each anneal step and transpile ising to fluxes
        for anneal_step in self.anneal_program:
            for circuit_element in anneal_step:
                phix, phiz = transpiler(
                    delta=anneal_step[circuit_element]["sigma_x"], epsilon=anneal_step[circuit_element]["sigma_z"]
                )
                anneal_step[circuit_element]["phix"] = phix
                anneal_step[circuit_element]["phiz"] = phiz
