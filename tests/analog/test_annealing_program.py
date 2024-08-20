"""Test the annealing program class"""
import numpy as np
import pytest

from qililab import AnnealingProgram
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


@pytest.fixture(name="anneal_program_dictionary_with_flux")
def get_anneal_program_dictionary_with_flux():
    """Dummy anneal program dictionary with transpiled fluxes"""
    return [
        {
            "qubit_0": {"sigma_x": 0, "sigma_y": 0, "sigma_z": 1, "phix": 1, "phiz": 0},
            "qubit_1": {"sigma_x": 0.1, "sigma_y": 0.1, "sigma_z": 0.1, "phix": 1.1, "phiz": 0.1},
            "coupler_0_1": {"sigma_x": 1, "sigma_y": 0.2, "sigma_z": 0.2, "phix": 1.2, "phiz": 0.2},
        },
        {
            "qubit_0": {"sigma_x": 0.1, "sigma_y": 0.1, "sigma_z": 1.1, "phix": 0.9, "phiz": 0.8},
            "qubit_1": {"sigma_x": 0.2, "sigma_y": 0.2, "sigma_z": 0.2, "phix": 0.7, "phiz": 0.6},
            "coupler_0_1": {"sigma_x": 0.9, "sigma_y": 0.1, "sigma_z": 0.1, "phix": 0.5, "phiz": 0.4},
        },
    ]


@pytest.fixture(name="annealing_program")
def dummy_annealing_program(anneal_program_dictionary):
    """Build dummy annealing program"""
    platform = build_platform(runcard=Galadriel.runcard)
    return AnnealingProgram(
        flux_to_bus_topology=platform.flux_to_bus_topology, annealing_program=anneal_program_dictionary
    )


@pytest.fixture(name="annealing_program_with_flux")
def dummy_annealing_program_with_flux(anneal_program_dictionary_with_flux):
    """Build dummy annealing program with fluxes already transpiled"""
    return AnnealingProgram(
        platform=build_platform(runcard=Galadriel.runcard), annealing_program=anneal_program_dictionary_with_flux
    )


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

    def test_transpile(self, annealing_program, anneal_program_dictionary):
        """Test transpile method"""
        annealing_program.transpile(transpiler=dummy_transpiler)
        assert sum(
            anneal_step[element]["phix"] == 2 * anneal_program_dictionary[i][element]["sigma_x"]
            for i, anneal_step in enumerate(anneal_program_dictionary)
            for element in anneal_step.keys()
        ) == len(anneal_program_dictionary) * len(anneal_program_dictionary[0])
        assert sum(
            anneal_step[element]["phiz"] == 3 * anneal_program_dictionary[i][element]["sigma_z"]
            for i, anneal_step in enumerate(anneal_program_dictionary)
            for element in anneal_step.keys()
        ) == len(anneal_program_dictionary) * len(anneal_program_dictionary[0])

    def test_get_waveforms(self, annealing_program_with_flux, anneal_program_dictionary_with_flux):
        """Test get waveforms method works as intended"""
        anneal_waveforms = annealing_program_with_flux.get_waveforms()
        anneal_waveforms = {key: (value[0].alias, value[1].envelope()) for key, value in anneal_waveforms.items()}

        phix_q0_waveform = (
            flux_to_bus("phix_q0"),
            np.array([anneal_step["qubit_0"]["phix"] for anneal_step in anneal_program_dictionary_with_flux]),
        )
        phiz_q0_waveform = (
            flux_to_bus("phiz_q0"),
            np.array([anneal_step["qubit_0"]["phiz"] for anneal_step in anneal_program_dictionary_with_flux]),
        )
        phix_q1_waveform = (
            flux_to_bus("phix_q1"),
            np.array([anneal_step["qubit_1"]["phix"] for anneal_step in anneal_program_dictionary_with_flux]),
        )
        phiz_q1_waveform = (
            flux_to_bus("phiz_q1"),
            np.array([anneal_step["qubit_1"]["phiz"] for anneal_step in anneal_program_dictionary_with_flux]),
        )
        phix_c0_1_waveform = (
            flux_to_bus("phix_c0_1"),
            np.array([anneal_step["coupler_0_1"]["phix"] for anneal_step in anneal_program_dictionary_with_flux]),
        )
        phiz_c0_1_waveform = (
            flux_to_bus("phiz_c0_1"),
            np.array([anneal_step["coupler_0_1"]["phiz"] for anneal_step in anneal_program_dictionary_with_flux]),
        )

        assert anneal_waveforms["phix_q0"][0] == phix_q0_waveform[0]
        np.allclose(anneal_waveforms["phix_q0"][1], phix_q0_waveform[1])
        assert anneal_waveforms["phiz_q0"][0] == phiz_q0_waveform[0]
        np.allclose(anneal_waveforms["phiz_q0"][1], phiz_q0_waveform[1])

        assert anneal_waveforms["phix_q1"][0] == phix_q1_waveform[0]
        np.allclose(anneal_waveforms["phix_q1"][1], phix_q1_waveform[1])
        assert anneal_waveforms["phiz_q1"][0] == phiz_q1_waveform[0]
        np.allclose(anneal_waveforms["phiz_q1"][1], phiz_q1_waveform[1])

        assert anneal_waveforms["phix_c0_1"][0] == phix_c0_1_waveform[0]
        np.allclose(anneal_waveforms["phix_c0_1"][1], phix_c0_1_waveform[1])
        assert anneal_waveforms["phiz_c0_1"][0] == phiz_c0_1_waveform[0]
        np.allclose(anneal_waveforms["phiz_c0_1"][1], phiz_c0_1_waveform[1])
