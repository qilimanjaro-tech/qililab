"""Tests for the QbloxDraw class."""

import numpy as np
import pytest
from qililab.data_management import build_platform
from tests.data import Galadriel, SauronQuantumMachines
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
    qp.set_gain("drive", 1)
    with qp.for_loop(frequency, FREQ_START, FREQ_STOP, FREQ_STEP):
        with qp.average(2):
            qp.reset_phase("drive")
            qp.set_frequency(bus="drive", frequency=frequency)
            qp.play(bus="drive", waveform=Square(amplitude=1, duration=5))
            qp.set_frequency(bus="drive", frequency=frequency)
            qp.wait("drive", 5)
            qp.play(bus="drive", waveform=Square(amplitude=1, duration=5))
    qp.set_frequency(bus="drive", frequency=frequency)
    return qp


@pytest.fixture(name="qp_plat_draw_qcmrf_offset")
def qp_plat_draw_qcmrf_offset() -> QProgram:
    qp = QProgram()
    qp.set_offset("drive_line_q1_bus", 0.5)
    qp.set_frequency("drive_line_q1_bus", 100e6)
    qp.play(bus="drive_line_q1_bus", waveform=Square(amplitude=1, duration=10))
    qp.wait("drive_line_q1_bus", 10)
    qp.wait("drive_line_q2_bus", 10)
    qp.set_offset("drive_line_q1_bus", 0)
    return qp

@pytest.fixture(name="qp_plat_draw_qcmrf")
def qp_plat_draw_qcmrf() -> QProgram:
    qp = QProgram()
    qp.set_phase("drive_line_q1_bus", 0.5)
    qp.set_frequency("drive_line_q1_bus", 100e6)
    qp.play(bus="drive_line_q1_bus", waveform=Square(amplitude=1, duration=10))
    qp.wait("drive_line_q1_bus", 10)
    qp.set_phase("drive_line_q1_bus", 0)
    return qp


@pytest.fixture(name="qp_plat_draw_qcm")
def qp_plat_draw_qcm() -> QProgram:
    qp = QProgram()
    qp.set_phase("drive_line_q0_bus", 0.5)
    qp.set_frequency("drive_line_q0_bus", 100e6)
    qp.play(bus="drive_line_q0_bus", waveform=Square(amplitude=1, duration=10))
    qp.wait("drive_line_q0_bus", 10)
    qp.set_phase("drive_line_q0_bus", 0)
    return qp

@pytest.fixture(name="qp_plat_draw_qcm_offset")
def qp_plat_draw_qcm_offset() -> QProgram:
    qp = QProgram()
    qp.set_offset("drive_line_q0_bus", 0.5)
    qp.set_frequency("drive_line_q0_bus", 100e6)
    qp.play(bus="drive_line_q0_bus", waveform=Square(amplitude=1, duration=10))
    qp.wait("drive_line_q0_bus", 10)
    qp.set_offset("drive_line_q0_bus", 0)
    return qp

@pytest.fixture(name="qp_plat_draw_qrm")
def qp_plat_draw_qrm() -> QProgram:
    qp = QProgram()
    qp.play(bus="feedline_input_output_bus", waveform=Square(amplitude=1, duration=10))
    qp.wait("feedline_input_output_bus", 10)
    return qp

@pytest.fixture(name="qp_quantum_machine")
def qp_quantum_machine() -> QProgram:
    qp = QProgram()
    qp.play(bus="drive_q0", waveform=Square(amplitude=1, duration=10))
    qp.wait("drive_q0", 10)
    return qp

@pytest.fixture(name="platform")
def fixture_platform():
    return build_platform(runcard=Galadriel.runcard)

@pytest.fixture(name="platform_quantum_machines")
def fixture_platform_quantum_machines():
    return build_platform(runcard=SauronQuantumMachines.runcard)
class TestQBloxDraw:
    def test_parsing(self, parsing: QProgram):
        compiler = QbloxCompiler()
        draw = QbloxDraw()
        sequences, _ = compiler.compile(qprogram=parsing)
        parsing = draw._parse_program(sequences)
        expected_parsing = [
            ("move", "3, R0", (), 0),
            ("move", "400000000, R1", (), 1),
            ("set_freq", "R1", ("loop_0",), 2),
            ("set_freq", "R1", ("loop_0",), 3),
            ("play", "0, 1, 10", ("loop_0",), 4),
            ("wait", "10", ("loop_0",), 5),
            ("add", "R1, 200000000, R1", ("loop_0",), 6),
            ("loop", "R0, @loop_0", ("loop_0",), 7),
            ("nop", "2", (), 8),
        ]
        assert parsing["drive"]["program"]["main"] == expected_parsing

    def test_qp_draw(self, qp_draw: QProgram):
        data_draw = qp_draw.draw()
        expected_data_draw_i = [ 7.07106781e-01,  5.72061403e-01,  2.18508012e-01, -2.18508012e-01,
       -5.72061403e-01, -0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
        0.00000000e+00,  0.00000000e+00,  7.07106781e-01,  5.72061403e-01,
        2.18508012e-01, -2.18508012e-01, -5.72061403e-01, -7.07106781e-01,
       -5.72061403e-01, -2.18508012e-01,  2.18508012e-01,  5.72061403e-01,
        0.00000000e+00,  0.00000000e+00,  0.00000000e+00, -0.00000000e+00,
       -0.00000000e+00, -7.07106781e-01, -5.72061403e-01, -2.18508012e-01,
        2.18508012e-01,  5.72061403e-01, -7.07106781e-01, -4.15626938e-01,
        2.18508012e-01,  6.72498512e-01,  5.72061403e-01, -0.00000000e+00,
       -0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
        7.07106781e-01,  4.15626938e-01, -2.18508012e-01, -6.72498512e-01,
       -5.72061403e-01, -2.42511464e-15,  5.72061403e-01,  6.72498512e-01,
        2.18508012e-01, -4.15626938e-01, -0.00000000e+00,  0.00000000e+00,
        0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  1.72753526e-16,
       -5.72061403e-01, -6.72498512e-01, -2.18508012e-01,  4.15626938e-01,
        7.07106781e-01,  2.18508012e-01, -5.72061403e-01, -5.72061403e-01,
        2.18508012e-01,  0.00000000e+00,  0.00000000e+00, -0.00000000e+00,
        0.00000000e+00,  0.00000000e+00,  7.07106781e-01,  2.18508012e-01,
       -5.72061403e-01, -5.72061403e-01,  2.18508012e-01,  7.07106781e-01,
        2.18508012e-01, -5.72061403e-01, -5.72061403e-01,  2.18508012e-01,
        0.00000000e+00,  0.00000000e+00, -0.00000000e+00,  0.00000000e+00,
        0.00000000e+00,  7.07106781e-01,  2.18508012e-01, -5.72061403e-01,
       -5.72061403e-01,  2.18508012e-01]
        expected_data_draw_q = [ 0.00000000e+00,  4.15626938e-01,  6.72498512e-01,  6.72498512e-01,
        4.15626938e-01,  0.00000000e+00, -0.00000000e+00, -0.00000000e+00,
        0.00000000e+00,  0.00000000e+00, -1.73191211e-16,  4.15626938e-01,
        6.72498512e-01,  6.72498512e-01,  4.15626938e-01,  1.51586078e-15,
       -4.15626938e-01, -6.72498512e-01, -6.72498512e-01, -4.15626938e-01,
        0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
        0.00000000e+00,  1.68905200e-15, -4.15626938e-01, -6.72498512e-01,
       -6.72498512e-01, -4.15626938e-01,  3.29150838e-15, -5.72061403e-01,
       -6.72498512e-01, -2.18508012e-01,  4.15626938e-01,  0.00000000e+00,
        0.00000000e+00, -0.00000000e+00, -0.00000000e+00,  0.00000000e+00,
       -1.03914727e-15,  5.72061403e-01,  6.72498512e-01,  2.18508012e-01,
       -4.15626938e-01, -7.07106781e-01, -4.15626938e-01,  2.18508012e-01,
        6.72498512e-01,  5.72061403e-01,  0.00000000e+00, -0.00000000e+00,
        0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  7.07106781e-01,
        4.15626938e-01, -2.18508012e-01, -6.72498512e-01, -5.72061403e-01,
       -1.21268863e-14,  6.72498512e-01,  4.15626938e-01, -4.15626938e-01,
       -6.72498512e-01,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
       -0.00000000e+00,  0.00000000e+00, -2.42467696e-15,  6.72498512e-01,
        4.15626938e-01, -4.15626938e-01, -6.72498512e-01, -7.62216404e-15,
        6.72498512e-01,  4.15626938e-01, -4.15626938e-01, -6.72498512e-01,
        0.00000000e+00,  0.00000000e+00,  0.00000000e+00, -0.00000000e+00,
        0.00000000e+00, -1.80171382e-14,  6.72498512e-01,  4.15626938e-01,
       -4.15626938e-01, -6.72498512e-01]
        
        compiler = QbloxCompiler()
        qblox_draw = QbloxDraw()
        results = compiler.compile(qp_draw)
        data_draw = qblox_draw.draw(results, None, True)
        np.testing.assert_allclose(data_draw["drive"][0], expected_data_draw_i, rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(data_draw["drive"][1], expected_data_draw_q, rtol=1e-2, atol=1e-12)

    def test_platform_draw_qcmrf(self, qp_plat_draw_qcmrf: QProgram, platform: Platform):
        expected_data_draw_i =[0.60062054, 0.60030277, 0.59986935, 0.59948583, 0.59929871,
       0.59937946, 0.59969723, 0.60013065, 0.60051417, 0.60070129,
       0.6       , 0.6       , 0.6       , 0.6       , 0.6       ,
       0.6       , 0.6       , 0.6       , 0.6       , 0.6       ]
        expected_data_draw_q = [ 3.39005047e-04,  6.39007798e-04,  6.94931289e-04,  4.85414647e-04,
        9.04861091e-05, -3.39005047e-04, -6.39007798e-04, -6.94931289e-04,
       -4.85414647e-04, -9.04861091e-05,  0.00000000e+00,  0.00000000e+00,
        0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
        0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00]

        data_draw = platform.draw(qp_plat_draw_qcmrf)
        np.testing.assert_allclose(data_draw["drive_line_q1_bus"][0], expected_data_draw_i, rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(data_draw["drive_line_q1_bus"][1], expected_data_draw_q, rtol=1e-2, atol=1e-12)

    def test_platform_draw_qcmrf_offset(self, qp_plat_draw_qcmrf_offset: QProgram, platform: Platform):
        expected_data_draw_i_q1 = [0.95424971, 0.67878691, 0.37323019, 0.15429183, 0.10559884,
       0.24575029, 0.52121309, 0.82676981, 1.        , 1.        ,
       0.9535426 , 0.67821485, 0.37301168, 0.15451033, 0.1061709 ,
       0.2464574 , 0.52178515, 0.82698832, 1.        , 1.        ]
        expected_data_draw_q_q1 = [ 0.3535426 ,  0.49424473,  0.44616216,  0.22766082, -0.07779922,
       -0.3535426 , -0.49424473, -0.44616216, -0.22766082,  0.07779922,
        0.3535426 ,  0.4938291 ,  0.44548967,  0.22698832, -0.07821485,
       -0.3535426 , -0.4938291 , -0.44548967, -0.22698832,  0.07821485]
        expected_data_draw_i_q2 = [0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6]
        expected_data_draw_q_q2 = [0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]
        
        data_draw = platform.draw(qp_plat_draw_qcmrf_offset)
        np.testing.assert_allclose(data_draw["drive_line_q1_bus"][0], expected_data_draw_i_q1, rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(data_draw["drive_line_q1_bus"][1], expected_data_draw_q_q1, rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(data_draw["drive_line_q2_bus"][0], expected_data_draw_i_q2, rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(data_draw["drive_line_q2_bus"][1], expected_data_draw_q_q2, rtol=1e-2, atol=1e-12)

    def test_platform_draw_qcm(self, qp_plat_draw_qcm: QProgram, platform: Platform):
        expected_data_draw_i = [2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 0. , 0. , 0. ,
       0. , 0. , 0. , 0. , 0. , 0. , 0. ]

        data_draw = platform.draw(qp_plat_draw_qcm)
        np.testing.assert_allclose(data_draw["drive_line_q0_bus"][0], expected_data_draw_i, rtol=1e-9, atol=1e-12)
        assert data_draw["drive_line_q0_bus"][1] is None

    def test_platform_draw_qcm_offset(self, qp_plat_draw_qcm_offset: QProgram, platform: Platform):
        expected_data_draw_i = [2.5       , 2.5       , 2.5       , 2.5       , 2.5       ,
       2.5       , 2.5       , 2.5       , 2.5       , 2.5       ,
       1.24996185, 1.24996185, 1.24996185, 1.24996185, 1.24996185,
       1.24996185, 1.24996185, 1.24996185, 1.24996185, 1.24996185]

        data_draw = platform.draw(qp_plat_draw_qcm_offset)
        np.testing.assert_allclose(data_draw["drive_line_q0_bus"][0], expected_data_draw_i, rtol=1e-2, atol=1e-12)
        assert data_draw["drive_line_q0_bus"][1] is None

    def test_get_value(self):
        draw = QbloxDraw()
        register = {}
        register["avg_no_loop"] = 1
        assert draw._get_value(None, register) is None

    def test_qp_plat_draw_qrm(self, qp_plat_draw_qrm: QProgram, platform: Platform):
        expected_data_draw_i = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.123 , 0.123 , 0.123 ,
       0.123 , 0.123 , 0.123 , 0.123 , 0.123 , 0.123 , 0.123]

        data_draw = platform.draw(qp_plat_draw_qrm)
        np.testing.assert_allclose(data_draw["feedline_input_output_bus"][0], expected_data_draw_i, rtol=1e-2, atol=1e-12)
        assert data_draw["feedline_input_output_bus"][1] is None

    def platform_draw_quantum_machine_raises_error(self, qp_quantum_machine: QProgram, platform_quantum_machines: Platform):
        with pytest.raises(
            NotImplementedError("The drawing feature is currently only supported for QBlox.")
        ):
            platform_quantum_machines.draw(qp_quantum_machine)
