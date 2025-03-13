"""Tests for the QbloxDraw class."""

import numpy as np
import pytest
from qililab.data_management import build_platform
from tests.data import Galadriel
from qililab import Domain, QbloxCompiler, QProgram, Square
from qililab.instruments.qblox.qblox_draw import QbloxDraw
from qililab.platform import Platform


@pytest.fixture(name="parsing")
def fixture_parsing() -> QProgram:
    qp = QProgram()
    frequency = qp.variable(label="drive", domain=Domain.Frequency)
    FREQ_START = 100e6
    FREQ_STOP = 200e6
    FREQ_STEP = 50e6
    with qp.for_loop(frequency, FREQ_START, FREQ_STOP, FREQ_STEP):
        with qp.average(2):
            qp.set_frequency(bus="drive", frequency=frequency)
            qp.play(bus="drive", waveform=Square(amplitude=1, duration=10))
            qp.wait("drive", 10)
    return qp


@pytest.fixture(name="qp_draw")
def qp_draw() -> QProgram:
    qp = QProgram()
    frequency = qp.variable(label="drive", domain=Domain.Frequency)
    FREQ_START = 100e6
    FREQ_STOP = 200e6
    FREQ_STEP = 50e6
    qp.set_gain("drive",1)
    with qp.for_loop(frequency, FREQ_START, FREQ_STOP, FREQ_STEP):
        with qp.average(2):
            qp.reset_phase("drive")
            qp.set_frequency(bus="drive", frequency=frequency)
            qp.play(bus="drive", waveform= Square(amplitude=1, duration=10))
            qp.set_frequency(bus="drive", frequency=frequency)
            qp.wait("drive",10)
            qp.play(bus="drive", waveform= Square(amplitude=1, duration=5))
    qp.set_frequency(bus="drive", frequency=frequency)
    return qp


@pytest.fixture(name="qp_plat_draw_qrmrf")
def qp_plat_draw_qrmrf() -> QProgram:
    qp = QProgram()
    qp.set_phase("drive_line_q1_bus",0.5)
    qp.set_frequency("drive_line_q1_bus",100e6)
    qp.play(bus="drive_line_q1_bus", waveform=Square(amplitude=1, duration=10))
    qp.wait("drive_line_q1_bus", 10)
    qp.set_phase("drive_line_q1_bus",0)
    return qp

@pytest.fixture(name="qp_plat_draw_qcm")
def qp_plat_draw_qcm() -> QProgram:
    qp = QProgram()
    qp.set_phase("drive_line_q0_bus",0.5)
    qp.set_frequency("drive_line_q0_bus",100e6)
    qp.play(bus="drive_line_q0_bus", waveform=Square(amplitude=1, duration=10))
    qp.wait("drive_line_q0_bus", 10)
    qp.set_phase("drive_line_q0_bus",0)
    return qp

@pytest.fixture(name="platform")
def fixture_platform():
    return build_platform(runcard=Galadriel.runcard)


class TestQBloxDraw:
    def test_parsing(self, parsing: QProgram):
        compiler = QbloxCompiler()
        draw = QbloxDraw()
        sequences, _ = compiler.compile(qprogram=parsing)
        parsing = draw._parse_program(sequences)
        expected_parsing = [
            ("move", "3, R0", (), 0),
            ("move", "400000000, R1", (), 1),
            ("move", "2, R2", ("loop_0",), 2),
            ("set_freq", "R1", ("loop_0", "avg_0"), 3),
            ("play", "0, 1, 10", ("loop_0", "avg_0"), 4),
            ("wait", "10", ("loop_0", "avg_0"), 5),
            ("loop", "R2, @avg_0", ("loop_0", "avg_0"), 6),
            ("add", "R1, 200000000, R1", ("loop_0",), 7),
            ("loop", "R0, @loop_0", ("loop_0",), 8),
            ("set_mrk", "0", (), 9),
            ("upd_param", "4", (), 10),
            ("stop", "", (), 11),
        ]
        assert parsing["drive"]["program"]["main"] == expected_parsing

    def test_qp_draw(self, qp_draw: QProgram):
        data_draw = qp_draw.draw_oscilloscope()
        expected_data_draw_i = [ 1.8 ,  1.46,  0.56, -0.56, -1.46, -1.8 , -1.46, -0.56,  0.56,
        1.46,  0.  ,  0.  ,  0.  ,  0.  ,  0.  ,  0.  , -1.46, -0.56,
        0.56,  1.46,  1.8 ,  1.06, -0.56, -1.71, -1.46, -0.  ,  1.46,
        1.71,  0.56, -1.06, -1.8 ,  0.  ,  0.  ,  0.  ,  0.  ,  0.  ,
        0.  , -1.71, -0.56,  1.06,  1.8 ,  1.06, -1.46, -1.46,  0.56,
        1.8 ,  0.56, -1.46, -1.46,  0.56,  1.8 ,  0.56,  0.  ,  0.  ,
        0.  ,  0.  ,  0.  ,  0.  , -1.46,  0.56,  1.8 ,  0.56, -1.46]
        expected_data_draw_q = [ 0.  ,  1.06,  1.71,  1.71,  1.06,  0.  , -1.06, -1.71, -1.71,
       -1.06,  0.  ,  0.  ,  0.  ,  0.  ,  0.  ,  0.  , -1.06, -1.71,
       -1.71, -1.06, -0.  ,  1.46,  1.71,  0.56, -1.06, -1.8 , -1.06,
        0.56,  1.71,  1.46,  0.  ,  0.  ,  0.  ,  0.  ,  0.  ,  0.  ,
        0.  , -0.56, -1.71, -1.46, -0.  ,  1.46,  1.06, -1.06, -1.71,
       -0.  ,  1.71,  1.06, -1.06, -1.71, -0.  ,  1.71,  0.  ,  0.  ,
        0.  ,  0.  ,  0.  ,  0.  , -1.06, -1.71, -0.  ,  1.71,  1.06]
        
        compiler = QbloxCompiler()
        draw = QbloxDraw()
        results = compiler.compile(qp_draw)
        data_draw = draw.draw_oscilloscope(results)
        np.testing.assert_allclose(data_draw["drive"][0], expected_data_draw_i, rtol=1e-2, atol=1e-2)
        np.testing.assert_allclose(data_draw["drive"][1], expected_data_draw_q, rtol=1e-2, atol=1e-2)

    def test_platform_draw_qrmrf(self, qp_plat_draw_qrmrf: QProgram, platform: Platform):
        expected_data_draw_i = [ 0.00157965,  0.00077072, -0.00033259, -0.00130887, -0.0017852 ,
       -0.00157965, -0.00077072,  0.00033259,  0.00130887,  0.0017852 ,
        0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
        0.        ,  0.        ,  0.        ,  0.        ,  0.        ]
        expected_data_draw_q = [ 0.00086297,  0.00162665,  0.00176901,  0.00123566,  0.00023034,
       -0.00086297, -0.00162665, -0.00176901, -0.00123566, -0.00023034,
        0.        ,  0.        ,  0.        ,  0.        ,  0.        ,
        0.        ,  0.        ,  0.        ,  0.        ,  0.        ]

        data_draw = platform.draw_oscilloscope_platform(qp_plat_draw_qrmrf)
        np.testing.assert_allclose(data_draw["drive_line_q1_bus"][0], expected_data_draw_i, rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(data_draw["drive_line_q1_bus"][1], expected_data_draw_q, rtol=1e-2, atol=1e-12)

    def test_platform_draw_qcm(self, qp_plat_draw_qcm: QProgram, platform: Platform):
        expected_data_draw_i = [2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 0. , 0. , 0. ,
       0. , 0. , 0. , 0. , 0. , 0. , 0. ]

        data_draw = platform.draw_oscilloscope_platform(qp_plat_draw_qcm)
        np.testing.assert_allclose(data_draw["drive_line_q0_bus"][0], expected_data_draw_i, rtol=1e-9, atol=1e-12)
        assert data_draw["drive_line_q0_bus"][1] is None

    def test_get_value(self):
        draw = QbloxDraw()
        register = {}
        register["avg_no_loop"] = 1
        assert draw._get_value(None, register) is None
