"""Test the annealing program class"""
from unittest.mock import patch

import numpy as np
import pytest

import qililab
from qililab import AnnealingProgram
from qililab.qprogram import CrosstalkMatrix
from qililab.settings import Runcard
from tests.data import Galadriel
from tests.test_utils import build_platform


@pytest.fixture(name="anneal_program_dictionary")
def get_anneal_program_dictionary():
    """Dummy anneal program dictionary"""
    return [
        {
            "qubit_0": {"sigma_x": 0, "sigma_y": 0, "sigma_z": 1},
            "qubit_1": {"sigma_x": 0.1, "sigma_y": 0.1, "sigma_z": 0.1},
            "coupler_0_1": {"sigma_x": 1, "sigma_y": 0.2, "sigma_z": 0.2},
        },
        {
            "qubit_0": {"sigma_x": 0.1, "sigma_y": 0.1, "sigma_z": 1.1},
            "qubit_1": {"sigma_x": 0.2, "sigma_y": 0.2, "sigma_z": 0.2},
            "coupler_0_1": {"sigma_x": 0.9, "sigma_y": 0.1, "sigma_z": 0.1},
        },
        {
            "qubit_0": {"sigma_x": 0.3, "sigma_y": 0.3, "sigma_z": 0.7},
            "qubit_1": {"sigma_x": 0.5, "sigma_y": 0.2, "sigma_z": 0.01},
            "coupler_0_1": {"sigma_x": 0.5, "sigma_y": 0, "sigma_z": -1},
        },
    ]


@pytest.fixture(name="flux_to_bus_topology")
def get_flux_to_bus_topology():
    flux_control_topology_didct = [
        {"flux": "phix_q0", "bus": "flux_line_phix_q0"},
        {"flux": "phiz_q0", "bus": "flux_line_phiz_q0"},
        {"flux": "phix_q1", "bus": "flux_line_phix_q1"},
        {"flux": "phiz_q1", "bus": "flux_line_phiz_q1"},
        {"flux": "phix_c0_1", "bus": "flux_line_phix_c0_1"},
        {"flux": "phiz_c0_1", "bus": "flux_line_phiz_c0_1"},
    ]
    return [Runcard.FluxControlTopology(**flux_control) for flux_control in flux_control_topology_didct]


@pytest.fixture(name="transpiled_program_dictionary")
def get_transpiled_program_dictionary():
    """Transpiled program for the anneal program above"""
    return [
        {
            "phix_q0": 0,
            "phiz_q0": 3,
            "phix_q1": 0.2,
            "phiz_q1": 0.30000000000000004,
            "phix_c0_1": 2,
            "phiz_c0_1": 0.6000000000000001,
        },
        {
            "phix_q0": 0.2,
            "phiz_q0": 3.3000000000000003,
            "phix_q1": 0.4,
            "phiz_q1": 0.6000000000000001,
            "phix_c0_1": 1.8,
            "phiz_c0_1": 0.30000000000000004,
        },
        {
            "phix_q0": 0.6,
            "phiz_q0": 2.0999999999999996,
            "phix_q1": 1.0,
            "phiz_q1": 0.03,
            "phix_c0_1": 1.0,
            "phiz_c0_1": -3,
        },
    ]


@pytest.fixture(name="annealing_program")
def get_annealing_program(flux_to_bus_topology, anneal_program_dictionary):
    """Build dummy annealing program"""
    return AnnealingProgram(flux_to_bus_topology=flux_to_bus_topology, annealing_program=anneal_program_dictionary)


@pytest.fixture(name="annealing_program_transpiled")
def get_annealing_program_transpiled(flux_to_bus_topology, anneal_program_dictionary, transpiled_program_dictionary):
    """Build dummy annealing program with fluxes already transpiled"""
    annealing_program = AnnealingProgram(
        flux_to_bus_topology=flux_to_bus_topology, annealing_program=anneal_program_dictionary
    )
    annealing_program._transpiled_program = transpiled_program_dictionary
    return annealing_program


def flux_to_bus(flux):
    """Return the corresponding bus to a given flux from the runcard topology"""
    return next(element["bus"] for element in Galadriel.runcard["flux_control_topology"] if element["flux"] == flux)


def dummy_transpiler(delta, epsilon):
    """Dummy transpiler for testing"""
    return (2 * delta, 3 * epsilon)


class TestAnnealingProgram:
    """Test class for the AnnealingProgram class"""

    def test_init(self, annealing_program, anneal_program_dictionary):
        """Test init method"""
        assert [flux_bus.to_dict() for flux_bus in annealing_program._flux_to_bus_topology] == Galadriel.runcard[
            "flux_control_topology"
        ]
        assert annealing_program._annealing_program == anneal_program_dictionary

    def test_transpile(self, annealing_program, transpiled_program_dictionary):
        """Test transpile method"""
        annealing_program.transpile(transpiler=dummy_transpiler)
        assert annealing_program._transpiled_program == transpiled_program_dictionary

    def test_get_waveforms(self, annealing_program_transpiled):
        """Test get waveforms method works as intended"""
        anneal_waveforms = annealing_program_transpiled.get_waveforms(correct_xtalk=False)
        transpiled_program = annealing_program_transpiled._transpiled_program

        phix_q0_waveform = (
            "flux_line_phix_q0",
            np.array([anneal_step["phix_q0"] for anneal_step in transpiled_program]),
        )
        phiz_q0_waveform = (
            "flux_line_phiz_q0",
            np.array([anneal_step["phiz_q0"] for anneal_step in transpiled_program]),
        )
        phix_q1_waveform = (
            "flux_line_phix_q1",
            np.array([anneal_step["phix_q1"] for anneal_step in transpiled_program]),
        )
        phiz_q1_waveform = (
            "flux_line_phiz_q1",
            np.array([anneal_step["phiz_q1"] for anneal_step in transpiled_program]),
        )
        phix_c0_1_waveform = (
            "flux_line_phix_c0_1",
            np.array([anneal_step["phix_c0_1"] for anneal_step in transpiled_program]),
        )
        phiz_c0_1_waveform = (
            "flux_line_phiz_c0_1",
            np.array([anneal_step["phiz_c0_1"] for anneal_step in transpiled_program]),
        )
        assert np.allclose(anneal_waveforms[phix_q0_waveform[0]].envelope(), phix_q0_waveform[1])
        assert np.allclose(anneal_waveforms[phiz_q0_waveform[0]].envelope(), phiz_q0_waveform[1])
        assert np.allclose(anneal_waveforms[phix_q1_waveform[0]].envelope(), phix_q1_waveform[1])
        assert np.allclose(anneal_waveforms[phiz_q1_waveform[0]].envelope(), phiz_q1_waveform[1])
        assert np.allclose(anneal_waveforms[phix_c0_1_waveform[0]].envelope(), phix_c0_1_waveform[1])
        assert np.allclose(anneal_waveforms[phiz_c0_1_waveform[0]].envelope(), phiz_c0_1_waveform[1])

    def test_get_waveforms_xtalk(self, annealing_program_transpiled):
        """Test get waveforms method works as intended"""
        # with patch(qililab.qprogram.crosstalk_matrix.CrosstalkMatrix, "from_buses") as dummy_xtalk_matrix:
        with patch.object(CrosstalkMatrix, "from_buses") as xtalk_from_buses:
            _ = annealing_program_transpiled.get_waveforms(correct_xtalk=True)
        # check that __matmul__ is called at each anneal step
        assert [call[0] for call in xtalk_from_buses.mock_calls].count("().inverse().__matmul__().items") == len(
            annealing_program_transpiled._transpiled_program
        )