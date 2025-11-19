# test_qprogram_results_to_samples.py
# Tests for qililab.digital.qprogram_results_to_samples using function-style pytest tests.
# Note: We use simple "dummy" results/measurement stubs that match the attributes the function needs
# (duck typing), so we don't rely on the real QProgramResults/QbloxMeasurementResult classes.

import numpy as np
import pytest

from qililab.digital import qprogram_results_to_samples


# ----------------------------
# Minimal stubs & test helpers
# ----------------------------
class _DummyMeasurement:
    def __init__(self, threshold):
        # The function only reads `.threshold` and does np.asarray(...).ravel().astype(np.uint8)
        self.threshold = threshold


class _DummyQProgramResults:
    def __init__(self):
        # Matches the structure the function expects: dict[str, list[measurement_like]]
        self.results = {}

    def append_result(self, bus: str, measurement: _DummyMeasurement):
        self.results.setdefault(bus, []).append(measurement)


def _build_results(bus_to_array: dict[str, np.ndarray]) -> _DummyQProgramResults:
    r = _DummyQProgramResults()
    for bus, arr in bus_to_array.items():
        r.append_result(bus, _DummyMeasurement(arr))
    return r


# Reusable sample arrays from the prompt examples
ARR_Q0 = np.array([0, 1, 1, 0, 0, 1, 1, 1, 1, 0], dtype=np.uint8)
ARR_Q1 = np.array([0, 1, 1, 0, 0, 0, 0, 0, 0, 0], dtype=np.uint8)


# ----------------------------
# Core happy-path scenarios
# ----------------------------
def test_two_qubits_default_order_q0_left_matches_example():
    results = _build_results(
        {
            "readout_q0_bus": ARR_Q0,
            "readout_q1_bus": ARR_Q1,
        }
    )
    mapping = {0: 0, 1: 1}
    out = qprogram_results_to_samples(results, mapping)
    assert out == {"00": 4, "10": 4, "11": 2}


def test_two_qubits_q0_right_order():
    results = _build_results(
        {
            "readout_q0_bus": ARR_Q0,
            "readout_q1_bus": ARR_Q1,
        }
    )
    mapping = {0: 0, 1: 1}
    out = qprogram_results_to_samples(results, mapping, order="q0-right")
    # With q0 as least-significant (rightmost) bit: pairs (q0,q1) -> bitstring q1q0
    assert out == {"00": 4, "01": 4, "11": 2}


def test_mapping_with_skip_missing_matches_example():
    # Only physical 3 and 4 are present; logical->physical includes a missing (2->0).
    results = _build_results(
        {
            "readout_q3_bus": ARR_Q0,
            "readout_q4_bus": ARR_Q1,
        }
    )
    mapping = {0: 3, 1: 4, 2: 0}
    out = qprogram_results_to_samples(results, mapping)  # on_missing='skip' by default
    # Missing logical qubit is dropped; remaining two qubits match the first example counts.
    assert out == {"00": 4, "10": 4, "11": 2}


def test_unordered_mapping_keys_are_sorted_internally():
    # Mapping insertion order reversed; function must sort logical keys ascending.
    results = _build_results(
        {
            "readout_q0_bus": ARR_Q0,
            "readout_q1_bus": ARR_Q1,
        }
    )
    mapping = {1: 1, 0: 0}
    out = qprogram_results_to_samples(results, mapping)
    assert out == {"00": 4, "10": 4, "11": 2}


# ----------------------------
# Missing-data behavior
# ----------------------------
def test_on_missing_error_raises_keyerror():
    # physical 2 is missing -> should raise KeyError when on_missing='error'
    results = _build_results({"readout_q0_bus": ARR_Q0})
    mapping = {0: 0, 1: 2}
    with pytest.raises(KeyError, match=r"physical qubit 2"):
        qprogram_results_to_samples(results, mapping, on_missing="error")


def test_on_missing_zeros_inserts_zero_column():
    # logical 2 -> physical 0 is missing; with zeros, an all-zero column (bit) is added.
    results = _build_results(
        {
            "readout_q3_bus": ARR_Q0,
            "readout_q4_bus": ARR_Q1,
        }
    )
    mapping = {0: 3, 1: 4, 2: 0}
    out = qprogram_results_to_samples(results, mapping, on_missing="zeros")
    # Three-bit strings: q0 (left), q1 (middle), q2=0 (right)
    assert out == {"000": 4, "100": 4, "110": 2}


def test_all_missing_with_skip_raises_no_data_valueerror():
    # No buses at all, and everything is missing -> "No measurement data found ..."
    results = _DummyQProgramResults()
    mapping = {0: 42}
    with pytest.raises(ValueError, match=r"No measurement data"):
        qprogram_results_to_samples(results, mapping, on_missing="skip")


def test_all_missing_with_zeros_still_raises_no_data_valueerror():
    # Even with on_missing='zeros', if nothing is present we cannot infer nshots -> same error.
    results = _DummyQProgramResults()
    mapping = {0: 7, 1: 9}
    with pytest.raises(ValueError, match=r"No measurement data"):
        qprogram_results_to_samples(results, mapping, on_missing="zeros")


def test_empty_bus_list_counts_as_missing_and_errors_when_requested():
    # Bus key exists but list is empty -> treated as missing; on_missing='error' must raise.
    results = _DummyQProgramResults()
    results.results["readout_q0_bus"] = []  # present but empty
    mapping = {0: 0}
    with pytest.raises(KeyError, match=r"physical qubit 0"):
        qprogram_results_to_samples(results, mapping, on_missing="error")


# ----------------------------
# Error handling & validation
# ----------------------------
def test_inconsistent_shots_raises_valueerror():
    arr0 = np.array([0, 1, 0, 1], dtype=np.uint8)         # 4 shots
    arr1 = np.array([0, 1, 0, 1, 0], dtype=np.uint8)      # 5 shots
    results = _build_results(
        {
            "readout_q0_bus": arr0,
            "readout_q1_bus": arr1,
        }
    )
    with pytest.raises(ValueError, match=r"Inconsistent number of shots"):
        qprogram_results_to_samples(results, {0: 0, 1: 1})


# ----------------------------
# Customization knobs
# ----------------------------
def test_custom_bus_fmt_is_used():
    results = _build_results(
        {
            "m7": ARR_Q0,
            "m9": ARR_Q1,
        }
    )
    mapping = {0: 7, 1: 9}
    out = qprogram_results_to_samples(results, mapping, bus_fmt="m{idx}")
    assert out == {"00": 4, "10": 4, "11": 2}


# ----------------------------
# Shape & dtype robustness
# ----------------------------
def test_non_flat_and_boolean_arrays_are_raveled_and_cast():
    # Provide non-flat (2D) boolean arrays; function should ravel and cast to uint8.
    arr0_bool_2d = np.array(
        [0, 1, 1, 0, 0, 1, 1, 1, 1, 0], dtype=bool
    ).reshape(2, 5)
    arr1_bool_2d = np.array(
        [0, 1, 1, 0, 0, 0, 0, 0, 0, 0], dtype=bool
    ).reshape(10, 1)

    results = _build_results(
        {
            "readout_q0_bus": arr0_bool_2d,
            "readout_q1_bus": arr1_bool_2d,
        }
    )
    out = qprogram_results_to_samples(results, {0: 0, 1: 1})
    assert out == {"00": 4, "10": 4, "11": 2}


# ----------------------------
# Single-qubit sanity check
# ----------------------------
def test_single_qubit_counts_are_correct():
    results = _build_results({"readout_q0_bus": ARR_Q0})
    out = qprogram_results_to_samples(results, {0: 0})
    # ARR_Q0 has six ones? Let's count: [0,1,1,0,0,1,1,1,1,0] -> zeros=4, ones=6
    assert out == {"0": 4, "1": 6}
