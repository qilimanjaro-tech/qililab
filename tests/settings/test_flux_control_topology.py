import pytest
from qililab.settings.analog.flux_control_topology import FluxControlTopology

@pytest.fixture(name="topology")
def fixture_topology() -> FluxControlTopology:
    return FluxControlTopology(flux="flux_0", bus="flux_bus_q0")

class TestFluxControlTopology:
    def test_init(self, topology: FluxControlTopology):
        topology.flux == "flux_0"
        topology.bus == "flux_bus_q0"

    def test_to_dict_method(self, topology: FluxControlTopology):
        as_dict = topology.to_dict()
        assert isinstance(as_dict, dict)
        assert as_dict["flux"] == "flux_0"
        assert as_dict["bus"] == "flux_bus_q0"
