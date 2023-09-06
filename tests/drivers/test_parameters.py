"""Unit test for drivers parameters"""
import inspect
import sys

from qililab.drivers import parameters


def test_parameters():
    interfaces = [member[0] for member in inspect.getmembers(sys.modules[parameters.__name__], inspect.isclass)]
    assert ["attenuator", "lo"] == interfaces

    # test specific parameters
    assert parameters.lo.frequency == "lo_frequency"
    assert parameters.attenuator.attenuation == "attenuation"
