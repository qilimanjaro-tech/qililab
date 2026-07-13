from qililab.utils import argsort_buses, sort_buses


def test_sort_buses():
    buses_to_sort = [
        # whitespace-separated
        "flux q0 x",
        "flux q0 z",
        "flux q0",
        "flux q1 x",
        "flux q2 z",
        "flux q10 x",
        "readout q0",
        "drive q0",
        "drive q1",
        "coupler 1 2 x",
        "coupler 1 10",
        "coupler 3 4",
        "ro 3",
        "d 4",
        "f 5 z",
        # underscore-separated
        "flux_q3_x",
        "flux_q4_z",
        "flux_q5",
        "flux_c0_1",
        "flux_c0_1_x",
        "flux_c1_2_z",
        "flux_c1_10",
        "drive_q6",
        "readout_q7",
        # mixed / short / uppercase
        "F Q8 X",
        "RO_9",
        "D 10",
        "Flux Q11 Z",
        # 'flux' trap: the x in flux/fluxonium must NOT count as a loop
        "fluxonium_12_z",
        "fluxonium 13",
        "flux0",
        "flux 1",
        # fall-back: no id
        "readout",
        "drive",
        "flux",
        # fall-back: alphabetic
        "a bus",
        "b bus",
    ]

    expected_sorting = [
        "readout",
        "drive",
        "flux",
        "a bus",
        "b bus",
        "readout q0",
        "drive q0",
        "flux q0 x",
        "flux q0 z",
        "flux q0",
        "flux0",
        "drive q1",
        "flux q1 x",
        "flux 1",
        "flux q2 z",
        "ro 3",
        "flux_q3_x",
        "d 4",
        "flux_q4_z",
        "f 5 z",
        "flux_q5",
        "drive_q6",
        "readout_q7",
        "F Q8 X",
        "RO_9",
        "D 10",
        "flux q10 x",
        "Flux Q11 Z",
        "fluxonium_12_z",
        "fluxonium 13",
        "flux_c0_1_x",
        "flux_c0_1",
        "flux_c1_2_z",
        "coupler 1 2 x",
        "flux_c1_10",
        "coupler 1 10",
        "coupler 3 4",
    ]

    sorted_buses = sort_buses(buses_to_sort)

    assert sorted_buses == expected_sorting


def test_argsort_buses_returns_permutation():
    buses = ["flux q10", "readout q10", "flux q2"]
    sorted_buses, order = argsort_buses(buses)
    assert sorted_buses == ["flux q2", "readout q10", "flux q10"]
    assert order == [2, 1, 0]
    assert [buses[i] for i in order] == sorted_buses
    assert sorted_buses == sort_buses(buses)


def test_criterion_1_fewer_indices_first():
    """Count of integers: no-index and single-index buses sort before two-index couplers."""
    assert sort_buses(["coupler 0 1", "flux q9", "flux"]) == ["flux", "flux q9", "coupler 0 1"]


def test_criterion_2_numeric_not_lexicographic():
    """Indices compare numerically, so q2 sorts before q10 (lexicographic would flip them)."""
    assert sort_buses(["flux q10", "flux q2", "flux q1"]) == ["flux q1", "flux q2", "flux q10"]


def test_criterion_3_bus_type_readout_drive_flux():
    """Type precedence at equal index: readout < drive < flux < unspecified."""
    assert sort_buses(["flux q0", "drive q0", "readout q0", "q0"]) == ["readout q0", "drive q0", "flux q0", "q0"]


def test_criterion_4_loop_type_x_before_z():
    """Loop precedence at equal type/index: x < z < unspecified."""
    assert sort_buses(["flux q0", "flux q0 z", "flux q0 x"]) == ["flux q0 x", "flux q0 z", "flux q0"]


def test_criterion_5_alphabetical_tiebreak():
    """When every other criterion ties, fall back to the raw string."""
    assert sort_buses(["b bus", "a bus"]) == ["a bus", "b bus"]
