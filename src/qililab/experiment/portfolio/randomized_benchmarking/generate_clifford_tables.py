"""
File used to compute the 'clifford_products.csv' and 'clifford_inverses.csv'.

clifford_products.csv: M[i][j] = k, where k is the index of Ck = Ci*Cj.

clifford_inverses.csv: M[i] = k, where k is the index of Ck = inverse(Ci).

The list of Clifford gates is defined in the 'cliffords.yaml' file.
"""
import logging
import pathlib
from typing import List

# from randomized_benchmarking import PRIMITIVE_GATES
import numpy as np
import yaml
from qibo.gates import RX, RY, I, M

PRIMITIVE_GATES = {
    "I": I(0),
    "X_pi/2": RX(0, np.pi / 2),
    "Y_pi/2": RY(0, np.pi / 2),
    "X_pi": RX(0, np.pi),
    "Y_pi": RY(0, np.pi),
}


def compare_matrices(mat1: np.ndarray, mat2: np.ndarray) -> bool:
    """
    Compares mat1 and mat2 taking into account global phases.
    We make sure that the absolute value and phase difference
    is the same for every value in the matrix.
    Returns True if mat1 == mat2 and False otherwise.
    """
    # Get rid of small decimals
    mat1 = np.round(mat1, 10)
    mat2 = np.round(mat2, 10)

    if mat1.shape != mat2.shape:
        return False

    # Flatten arrays
    mat1 = mat1.reshape(1, -1)
    mat2 = mat2.reshape(1, -1)

    try:
        # Compute phase difference of non-zero values
        phase_diff = np.angle(mat1[mat1 != 0]) - np.angle(mat2[mat2 != 0])
        # Move to [0, 2pi)
        phase_diff[phase_diff < 0] += 2 * np.pi
        phase_diff[phase_diff == 2 * np.pi] = 0
    except ValueError:  # TODO can this actually happen?
        return False

    return np.allclose(abs(mat1), abs(mat2)) and (phase_diff == phase_diff[0]).all()


def find_clifford_idx(matrix: np.ndarray, clifford_matrices: List[np.ndarray]) -> int:
    compare = [compare_matrices(matrix, c) for c in clifford_matrices]
    assert np.sum(compare) == 1  # make sure only 1 clifford gate is detected

    return compare.index(True)


def main() -> None:
    # Load values from YAML file
    with open(pathlib.Path(__file__).parent / "cliffords.yaml", "r") as file:
        try:
            f = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            logging.error(exc)

    prim_gates = f["primitive_gates"]
    clifford_gates = f["clifford_gates"]

    # Compute matrices of clifford gates
    clifford_matrices = []

    for gate in clifford_gates:
        gate_list = list(map(int, str(gate)))  # convert gate into list
        u = np.identity(2)
        # Reverse order of matrices
        for prim in gate_list[::-1]:
            u = u @ PRIMITIVE_GATES[prim_gates[prim]["name"]].matrix
        clifford_matrices.append(u)

    # Compute the inverse of all clifford gates
    # and the product of all possible pairs
    # and find to which clifford gate they correspond
    mul_matrix = np.full((len(clifford_gates), len(clifford_gates)), -1)
    inv_matrix = np.full(len(clifford_gates), -1)

    for x, matx in enumerate(clifford_matrices):
        for y, maty in enumerate(clifford_matrices):
            mul = matx @ maty
            inv = np.transpose(np.conjugate(matx))
            mul_matrix[x][y] = find_clifford_idx(matrix=mul, clifford_matrices=clifford_matrices)
            inv_matrix[x] = find_clifford_idx(matrix=inv, clifford_matrices=clifford_matrices)

    np.savetxt(pathlib.Path(__file__).parent / "clifford_products.csv", mul_matrix, delimiter=",", fmt="%i")
    np.savetxt(pathlib.Path(__file__).parent / "clifford_inverses.csv", inv_matrix, delimiter=",", fmt="%i")


if __name__ == "__main__":
    main()
