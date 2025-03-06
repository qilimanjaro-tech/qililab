"""Test the annealing program class"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from tests.data import Galadriel

from qililab import AnnealingProgram
from qililab.qprogram.crosstalk_matrix import FluxVector
from qililab.settings.analog.flux_control_topology import FluxControlTopology


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
    flux_control_topology_dict = [
        {"flux": "phix_q0", "bus": "flux_line_phix_q0"},
        {"flux": "phiz_q0", "bus": "flux_line_phiz_q0"},
        {"flux": "phix_q1", "bus": "flux_line_phix_q1"},
        {"flux": "phiz_q1", "bus": "flux_line_phiz_q1"},
        {"flux": "phix_c0_1", "bus": "flux_line_phix_c0_1"},
        {"flux": "phiz_c0_1", "bus": "flux_line_phiz_c0_1"},
    ]
    return [FluxControlTopology(**flux_control) for flux_control in flux_control_topology_dict]


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

    def test_init(self, annealing_program, anneal_program_dictionary, flux_to_bus_topology):
        """Test init method"""
        assert annealing_program._flux_to_bus_topology == flux_to_bus_topology
        assert annealing_program._annealing_program == anneal_program_dictionary

    def test_transpile(self, annealing_program, transpiled_program_dictionary):
        """Test transpile method"""
        annealing_program.transpile(transpiler=dummy_transpiler)
        assert annealing_program._transpiled_program == transpiled_program_dictionary

    @pytest.mark.parametrize("minimum_clock_time", [1, 3, 4, 10])
    def test_get_waveforms(self, annealing_program_transpiled, minimum_clock_time):
        """Test get waveforms method works as intended"""
        anneal_waveforms = annealing_program_transpiled.get_waveforms(minimum_clock_time=minimum_clock_time)
        transpiled_program = annealing_program_transpiled._transpiled_program

        pad_length = (
            minimum_clock_time - len(transpiled_program) % minimum_clock_time
            if len(transpiled_program) % minimum_clock_time != 0
            else 0
        )

        phix_q0_waveform = (
            "flux_line_phix_q0",
            np.array(pad_length * [0] + [anneal_step["phix_q0"] for anneal_step in transpiled_program]),
        )
        phiz_q0_waveform = (
            "flux_line_phiz_q0",
            np.array(pad_length * [0] + [anneal_step["phiz_q0"] for anneal_step in transpiled_program]),
        )
        phix_q1_waveform = (
            "flux_line_phix_q1",
            np.array(pad_length * [0] + [anneal_step["phix_q1"] for anneal_step in transpiled_program]),
        )
        phiz_q1_waveform = (
            "flux_line_phiz_q1",
            np.array(pad_length * [0] + [anneal_step["phiz_q1"] for anneal_step in transpiled_program]),
        )
        phix_c0_1_waveform = (
            "flux_line_phix_c0_1",
            np.array(pad_length * [0] + [anneal_step["phix_c0_1"] for anneal_step in transpiled_program]),
        )
        phiz_c0_1_waveform = (
            "flux_line_phiz_c0_1",
            np.array(pad_length * [0] + [anneal_step["phiz_c0_1"] for anneal_step in transpiled_program]),
        )
        assert np.allclose(anneal_waveforms[phix_q0_waveform[0]].envelope(), phix_q0_waveform[1])
        assert np.allclose(anneal_waveforms[phiz_q0_waveform[0]].envelope(), phiz_q0_waveform[1])
        assert np.allclose(anneal_waveforms[phix_q1_waveform[0]].envelope(), phix_q1_waveform[1])
        assert np.allclose(anneal_waveforms[phiz_q1_waveform[0]].envelope(), phiz_q1_waveform[1])
        assert np.allclose(anneal_waveforms[phix_c0_1_waveform[0]].envelope(), phix_c0_1_waveform[1])
        assert np.allclose(anneal_waveforms[phiz_c0_1_waveform[0]].envelope(), phiz_c0_1_waveform[1])

    def test_get_waveforms_same_bus_error(self, annealing_program_transpiled):
        """Test get waveforms method works as intended"""

        # point two fluxes to the same bus
        annealing_program_transpiled._flux_to_bus_topology[0].bus = annealing_program_transpiled._flux_to_bus_topology[
            1
        ].bus
        error_string = f"More than one flux pointing at bus {annealing_program_transpiled._flux_to_bus_topology[1].bus} in the runcard flux to bus topology"
        with pytest.raises(ValueError, match=error_string):
            _ = annealing_program_transpiled.get_waveforms()

    def test_get_waveforms_xtalk(self, annealing_program_transpiled):
        """Test get waveforms method works as intended"""
        crosstalk_matrix = MagicMock()
        with patch.object(FluxVector, "set_crosstalk") as mock_set_crosstalk:
            _ = annealing_program_transpiled.get_waveforms(crosstalk_matrix=crosstalk_matrix)
        # check that __matmul__ is called at each anneal step
        mock_set_crosstalk.assert_called()
