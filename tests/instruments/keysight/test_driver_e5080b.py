"""Tests for the DriverE5080B class."""

# This test along the driver code are meant to be qcodes
from qililab.instruments.keysight.driver_keysight_e5080b import Driver_KeySight_E5080B
import pytest
import numpy as np

@pytest.fixture(scope="function", name="vnaks")
def _make_vnaks():
    """
    Create a simulated Keysight E5080B instrument.
    The pyvisa_sim_file parameter instructs QCoDeS to use the simulation file.
    """
    driver = Driver_KeySight_E5080B(
        "Keysight_E5080B",
        address="TCPIP::192.168.0.10::INSTR",
        pyvisa_sim_file="qililab.instruments.keysight:Keysight_E5080B.yaml"
    )
    yield driver
    driver.close()

# def verify_property(vnaks, param_name, vals: "Sequence[Any]"):
#     print(vnaks.parameters)
#     print(param_name)
#     # param = getattr(vnaks, param_name)
#     param = vnaks.parameters["start_freq"]
#     print(param)
#     for val in vals:
#         param(val)
#         new_val = param()
#         if isinstance(new_val, float):
#             assert np.isclose(new_val, val)
#         else:
#             assert new_val == val

# def test_frequency(vnaks) -> None:
#     verify_property(vnaks, "start_freq", [1e6, 2e6, 3e9, 20e9])


def verify_property(vnaks, param_name, vals):
    """
    For each value in vals, set the parameter and verify that it returns the expected value.
    """
    # Access the parameter from the instrument's parameters dictionary
    param = vnaks.parameters[param_name]
    for val in vals:
        param(val)
        new_val = param()
        if isinstance(new_val, float):
            assert np.isclose(new_val, val), f"{param_name} expected {val}, got {new_val}"
        else:
            assert new_val == val, f"{param_name} expected {val}, got {new_val}"

def test_start_freq(vnaks):
    verify_property(vnaks, "start_freq", [1e6, 2e6, 3e9, 20e9])

def test_stop_freq(vnaks):
    verify_property(vnaks, "stop_freq", [1e6, 2e6, 3e9, 20e9])
