import pytest
from qililab.settings.digital.digital_compilation_bus_settings import DigitalCompilationBusSettings
from qililab.typings.enums import Line

class TestDigitalCompilationBusSettings:
    def test_init_raises_error_if_weights_have_different_length(self):
        settings = {
            "line": Line.READOUT,
            "qubits": [0],
            "weights_i": [x for x in range(10)],
            "weights_q": [x for x in range(20)],
            "weighed_acq_enabled": True
        }

        with pytest.raises(IndexError):
            _ = DigitalCompilationBusSettings(**settings)
