import pathlib
from unittest.mock import patch

import numpy as np
import pytest
from qibo.gates import RX, RY, I

from qililab.experiment.portfolio.randomized_benchmarking import generate_clifford_tables as gen_clifford


@pytest.fixture(name="primitive_gates")
def primitive_gates():
    # primitives are a subset of cliffords
    return {
        "I": I(0),
        "X_pi/2": RX(0, np.pi / 2),
        "Y_pi/2": RY(0, np.pi / 2),
        "X_pi": RX(0, np.pi),
        "Y_pi": RY(0, np.pi),
    }


@pytest.fixture(name="primitive_matrices")
def primitive_matrices(primitive_gates):
    # primitives are a subset of cliffords
    return [gate.matrix for gate in primitive_gates.values()]


@pytest.fixture(name="clifford_matrices")
def get_clifford_matrices(primitive_gates):
    clifford_matrices = []
    # calculate clifford matrices
    clifford_gates = [
        0,
        21,
        123,
        3,
        214,
        124,
        4,
        2134,
        12,
        34,
        213,
        1234,
        23,
        13,
        1214,
        24,
        1,
        121,
        234,
        14,
        12134,
        2,
        134,
        1213,
    ]
    prim_gates = {
        0: {"name": "I"},
        1: {"name": "X_pi/2"},
        2: {"name": "Y_pi/2"},
        3: {"name": "X_pi"},
        4: {"name": "Y_pi"},
    }
    for gate in clifford_gates:
        gate_list = list(map(int, str(gate)))  # convert gate into list
        u = np.identity(2)
        # Reverse order of matrices
        for prim in gate_list[::-1]:
            u = u @ primitive_gates[prim_gates[prim]["name"]].matrix
        clifford_matrices.append(u)
    return clifford_matrices


@pytest.fixture(name="clifford_gates")
def clifford_gates():
    return [0, 21, 123, 3, 214, 124, 4, 2134, 12, 34, 213, 1234, 23, 13, 1214, 24, 1, 121, 234, 14, 12134, 2, 134, 1213]


class MockWriter:
    """Mock writer for the np.savetxt call in main()"""

    def __init__(self) -> None:
        self.stored_data = []  # type: list[np.ndarray]

    def __call__(self, path, mul_matrix, delimiter=",", fmt="%i"):
        self.stored_data.append((path, mul_matrix))


class TestGenerateCliffordTables:
    @pytest.mark.parametrize(
        "mat1, mat2",
        [
            (np.array([[1, 0], [1, 1]]), np.array([[np.exp(1j * a), 0], [np.exp(1j * a), np.exp(1j * a)]]))
            for a in np.linspace(0, 2 * np.pi, 1)
        ],
    )
    def test_compare_matrices(self, mat1, mat2):
        """Test random matrices with random phase differences"""
        compare = bool(gen_clifford.compare_matrices(mat1, mat2))
        assert isinstance(compare, bool)
        assert compare

    def test_compare_matrices_return_false(self):
        """Test cases where false is returned"""
        # different shapes
        mat1 = np.array([[1, 1, 0], [1, 0, 0]])
        mat2 = np.array([[1, 0], [0, 1]])
        compare = bool(gen_clifford.compare_matrices(mat1, mat2))
        assert isinstance(compare, bool)
        assert not compare

        # local phase difference
        mat1 = np.array([[1, 0], [1, 0]])
        mat2 = np.array([[1, 1], [0, 1]])
        compare = bool(gen_clifford.compare_matrices(mat1, mat2))
        assert isinstance(compare, bool)
        assert not compare

    def test_find_clifford_idx(self, primitive_matrices):
        """Test for a subset of clifford matrices"""
        index = gen_clifford.find_clifford_idx(RX(0, np.pi).matrix, primitive_matrices)
        assert isinstance(index, int)  # check index is integer
        assert index == 3  # X_pi should be the 3rd index in primitive matrices

    @patch("numpy.savetxt", new_callable=MockWriter)
    def test_main(self, mock_txt, clifford_matrices):
        """Test that main writes the expected data for clifford products/inverses"""
        gen_clifford.main()

        clifford_products, clifford_inverses = mock_txt.stored_data

        # check paths are correct
        assert isinstance(clifford_products[0], pathlib.PosixPath)
        assert isinstance(clifford_inverses[0], pathlib.PosixPath)
        assert clifford_products[0].stem == "clifford_products"
        assert clifford_inverses[0].stem == "clifford_inverses"

        prods = clifford_products[1]
        invs = clifford_inverses[1]
        assert isinstance(prods, np.ndarray)
        assert isinstance(invs, np.ndarray)

        assert prods.shape == (24, 24)
        assert len(invs) == 24

        # neither neye or eye is fully true but their sum is.
        # This is because some inverses will be I and other -I
        # eg. I @ I^-1 = I; X_pi @ X_pi^-1 = X_pi @ X_pi = -I
        # note that they're still inverses up to a global phase
        prods = prods.reshape(24 * 24)
        inv_prods = np.array([invs[prod] for prod in prods])
        neye = np.array(
            [
                np.allclose(-np.eye(2), clifford_matrices[prods[n]] @ clifford_matrices[inv_prods[n]])
                for n in range(len(prods))
            ]
        )
        eye = np.array(
            [
                np.allclose(np.eye(2), clifford_matrices[prods[n]] @ clifford_matrices[inv_prods[n]])
                for n in range(len(prods))
            ]
        )
        assert (np.invert(neye * eye) * (neye + eye)).all()
