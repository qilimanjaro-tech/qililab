import numpy as np
import pytest
from qprogram.blocks import Average
from qprogram.operations import Sync
from qprogram_qdac import Play as QdacPlay
from qprogram_qdac import SetOffset as QdacSetOffset
from qprogram_qdac import SetTrigger as QdacSetTrigger

from qililab import Arbitrary, Calibration, IQPair, QProgram, Square
from qililab.qprogram.blocks import IfTrigger
from qililab.qprogram.crosstalk.crosstalk_matrix import CrosstalkMatrix
from qililab.qprogram.compilers.prepass import prepare_qdac

QDAC_BUSES_OFFSET = {"flux1": 0.0, "flux2": 0.0}


@pytest.fixture(name="flux_qprogram")
def fixture_flux_qprogram() -> QProgram:
    qp = QProgram()
    qp.qdac.set_offset(bus="flux2", offset=0.3)
    qp.qdac.play(bus="flux1", waveform=Arbitrary(samples=np.array([0.0, 0.1, 0.2, 0.1, 0.0])), dwell=2)
    return qp


class TestPrepareQdac:
    def test_keeps_only_operations_on_qdac_buses(self):
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=Square(amplitude=0.5, duration=10), dwell=2)
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, position="step", outputs=[1])
        with qp.if_trigger(expected_wait_time_ns=2252):
            with qp.average(shots=10):
                qp.qblox.acquire(bus="readout", weights=IQPair(I=Square(1.0, 100), Q=Square(0.0, 100)))
        qp.qdac.set_offset(bus="flux2", offset=0.2)
        qp.sync()

        result = prepare_qdac(qp, qdac_buses=["flux1", "flux2"], qdac_buses_offset=QDAC_BUSES_OFFSET)

        assert result.buses == {"flux1", "flux2"}
        assert [type(element) for element in result.body.elements] == [
            QdacPlay,
            QdacSetTrigger,
            IfTrigger,
            QdacSetOffset,
            Sync,
        ]
        conditional = result.body.elements[2]
        assert isinstance(conditional.elements[0], Average)
        assert conditional.elements[0].elements == []
        assert "readout" in qp.buses

    def test_crosstalk_uses_explicit_matrix(self, flux_qprogram: QProgram):
        crosstalk = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": 0.5}, "flux2": {"flux1": 0.1, "flux2": 1.0}}
        )
        dc_calibration = Calibration()
        dc_calibration.crosstalk_matrix = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": -0.3}, "flux2": {"flux1": 0.2, "flux2": 1.0}}
        )

        result = prepare_qdac(
            flux_qprogram,
            qdac_buses=["flux1", "flux2"],
            qdac_buses_offset=QDAC_BUSES_OFFSET,
            calibration=dc_calibration,
            crosstalk=crosstalk,
        )

        expected = flux_qprogram.with_crosstalk_qdac(crosstalk=crosstalk, qdac_buses_offset=QDAC_BUSES_OFFSET)
        assert str(result) == str(expected)

    def test_crosstalk_falls_back_to_calibration_dc_matrix(self, flux_qprogram: QProgram):
        crosstalk = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": 0.5}, "flux2": {"flux1": 0.1, "flux2": 1.0}}
        )
        calibration = Calibration()
        calibration.crosstalk_matrix = crosstalk

        result = prepare_qdac(
            flux_qprogram, qdac_buses=["flux1", "flux2"], qdac_buses_offset=QDAC_BUSES_OFFSET, calibration=calibration
        )

        expected = flux_qprogram.with_crosstalk_qdac(crosstalk=crosstalk, qdac_buses_offset=QDAC_BUSES_OFFSET)
        assert str(result) == str(expected)

    def test_calibration_ac_matrix_is_ignored(self, flux_qprogram: QProgram):
        calibration = Calibration()
        calibration.crosstalk_matrix_ac = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": 0.5}, "flux2": {"flux1": 0.1, "flux2": 1.0}}
        )

        result = prepare_qdac(
            flux_qprogram, qdac_buses=["flux1", "flux2"], qdac_buses_offset=QDAC_BUSES_OFFSET, calibration=calibration
        )

        assert str(result) == str(flux_qprogram)
