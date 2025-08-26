from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from qililab.platform import Bus
from qililab.waveforms import Square
from qililab.instruments import Instrument, Instruments
from qililab.instruments.qdevil.qdevil_qdac2 import QDevilQDac2
from qililab.qprogram import QProgram, Calibration, QdacCompiler


@pytest.fixture(name="qdac_instrument")
def mock_instrument() -> list[Instrument]:
    instrument1 = MagicMock(spec=QDevilQDac2)
    type(instrument1).alias = property(lambda self: "qdac")
    return [instrument1]


@pytest.fixture(name="flux1")
def fixture_bus_flux1(qdac_instrument) -> Bus:
    settings = {"alias": "flux1", "instruments": ["qdac"], "channels": [1]}
    return Bus(settings=settings, platform_instruments=Instruments(elements=qdac_instrument))


@pytest.fixture(name="flux2")
def fixture_bus_flux2(qdac_instrument) -> Bus:
    settings = {"alias": "flux2", "instruments": ["qdac"], "channels": [2]}
    return Bus(settings=settings, platform_instruments=Instruments(elements=qdac_instrument))


@pytest.fixture(name="qdac")
def fixture_qdac() -> QDevilQDac2:
    """Fixture that returns an instance of a dummy QDAC-II."""
    qdac = QDevilQDac2(
        {
            "alias": "qdac",
            "voltage": [0.5, 0.5, 0.5, 0.5],
            "span": ["low", "low", "low", "low"],
            "ramping_enabled": [True, True, True, False],
            "ramp_rate": [0.01, 0.01, 0.01, 0.01],
            "dacs": [1, 2, 3, 4],
            "low_pass_filter": ["dc", "dc", "dc", "dc"],
        }
    )
    qdac.device = MagicMock()
    return qdac


@pytest.fixture(name="calibration")
def fixture_calibration() -> Calibration:
    calibration = Calibration()
    calibration.add_waveform(bus="flux1", name="calibrated_square", waveform=Square(1.0, 100))

    return calibration


@pytest.fixture(name="calibrated_execution")
def fixture_calibrated_execution() -> QProgram:
    qp = QProgram()
    qp.play(bus="flux1", waveform="calibrated_square")
    return qp


class TestQdacCompiler:
    def test_play_and_set_trigger(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        pulse_wf = Square(1.0, 100)
        dwell_us = 2
        out_port = 1

        qp = QProgram()
        qp.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, outputs=out_port, position="start")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1, flux2])

        # compiler._qdac.set_start_marker_external_trigger.assert_called_once()
        # compiler._qdac.upload_voltage_list.assert_called_twice()


#     def test_qdac_bus_ignored(self, run_qdac_buses: QProgram):

#         mock_qdac_bus = MagicMock()
#         mock_qdac_bus.alias = "qdac_flux"

#         compiler = QbloxCompiler()
#         output = compiler.compile(
#             qprogram=run_qdac_buses, bus_mapping={"drive": "drive_q0"}, qdac_buses=[mock_qdac_bus]
#         )

#         assert len(output.sequences) == 1
#         assert "drive_q0" in output.sequences
#         assert isinstance(output.sequences["drive_q0"], QPy.Sequence)

#     def test_qdac_sync_raises_error(self, run_qdac_sync: QProgram):

#         mock_qdac_bus = MagicMock()
#         mock_qdac_bus.alias = "qdac_flux"

#         compiler = QbloxCompiler()

#         with pytest.raises(ValueError, match="QDACII buses not allowed inside sync function"):
#             compiler.compile(qprogram=run_qdac_sync, bus_mapping={"drive": "drive_q0"}, qdac_buses=[mock_qdac_bus])

#     def test_set_trigger(self, set_trigger: QProgram):

#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=set_trigger)
#         assert len(sequences) == 1
#         assert "drive" in sequences

#         drive_str = """
#                 setup:
#                                 wait_sync        4
#                                 set_mrk          0
#                                 upd_param        4

#                 main:
#                                 set_mrk          1
#                                 upd_param        4
#                                 wait             96
#                                 set_mrk          0
#                                 upd_param        4
#                                 wait             96
#                                 set_mrk          0
#                                 upd_param        4
#                                 stop
#             """
#         assert is_q1asm_equal(sequences["drive"]._program, drive_str)

#         # RF example with the right markers
#         sequences, _ = compiler.compile(qprogram=set_trigger, markers={"drive": "1100"})
#         assert len(sequences) == 1
#         assert "drive" in sequences

#         drive_str = """
#                 setup:
#                                 wait_sync        4
#                                 set_mrk          12
#                                 upd_param        4

#                 main:
#                                 set_mrk          13
#                                 upd_param        4
#                                 wait             96
#                                 set_mrk          12
#                                 upd_param        4
#                                 wait             96
#                                 set_mrk          0
#                                 upd_param        4
#                                 stop
#             """
#         assert is_q1asm_equal(sequences["drive"]._program, drive_str)

#     def test_set_trigger_raises_no_output_error(self):
#         qp = QProgram()
#         qp.set_trigger(bus="drive", duration=10)

#         compiler = QbloxCompiler()

#         with pytest.raises(ValueError, match="Missing qblox trigger outputs at qp.set_trigger."):
#             compiler.compile(qprogram=qp)

#     def test_set_trigger_raises_output_out_of_range_error(self):
#         qp = QProgram()
#         qp.set_trigger(bus="drive", duration=10, outputs=5)

#         compiler = QbloxCompiler()

#         with pytest.raises(ValueError, match="Low frequency modules only have 4 trigger outputs, out of range"):
#             compiler.compile(qprogram=qp)
#             pass

#         compiler._markers = {"drive": "1100"}
#         with pytest.raises(ValueError, match="RF modules only have 2 trigger outputs, either 1 or 2"):
#             compiler.compile(qprogram=qp, markers={"drive": "1100"})
#             pass

#     def test_wait_trigger(self, wait_trigger: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=wait_trigger, ext_trigger=True)

#         assert sequences["drive"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             set_freq         4000000
#                             set_freq         4000000
#                             upd_param        4
#                             wait_trigger     15, 4
#                             wait_sync        4
#                             set_freq         4000000
#                             set_freq         4000000
#                             upd_param        4
#                             wait_trigger     1, 996
#                             wait_sync        4
#                             set_freq         4000000
#                             set_freq         4000000
#                             upd_param        4
#                             wait_trigger     1, 4
#                             wait             65532
#                             wait             65532
#                             wait_sync        4
#                             wait_trigger     1, 1000
#                             wait_sync        4
#                             wait_trigger     1, 4
#                             wait             65532
#                             wait             65532
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """

#         readout_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             set_freq         4000000
#                             set_freq         4000000
#                             wait_sync        4
#                             wait_sync        4
#                             wait_sync        4
#                             wait_sync        4
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     def test_wait_trigger_no_ext_trigger_raises_error(self, wait_trigger: QProgram):

#         compiler = QbloxCompiler()
#         with pytest.raises(
#             AttributeError, match="External trigger has not been set as True inside runcard's instrument controllers."
#         ):
#             compiler.compile(qprogram=wait_trigger, ext_trigger=False)

#     def test_wait_trigger_var_durationraises_error(self):

#         qp = QProgram()
#         duration = qp.variable(label="duration", domain=Domain.Time)
#         with qp.for_loop(variable=duration, start=4, stop=100, step=4):
#             qp.wait_trigger(bus="drive", duration=duration, port=1)

#         compiler = QbloxCompiler()
#         with pytest.raises(ValueError, match="Wait trigger duration cannot be a Variable, it must be an int."):
#             compiler.compile(qprogram=qp, ext_trigger=True)

#     def test_block_handlers(self, measurement_blocked_operation: QProgram, calibration: Calibration):
#         drag_wf = IQPair.DRAG(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5)
#         readout_pair = IQPair(I=Square(amplitude=1.0, duration=1000), Q=Square(amplitude=0.0, duration=1000))
#         weights_pair = IQPair(I=Square(amplitude=1.0, duration=2000), Q=Square(amplitude=0.0, duration=2000))
#         qp_no_block = QProgram()
#         qp_no_block.play(bus="drive", waveform=drag_wf)
#         qp_no_block.measure(bus="readout", waveform=readout_pair, weights=weights_pair)

#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=measurement_blocked_operation)

#         sequences_no_block, _ = compiler.compile(qprogram=qp_no_block)
#         assert len(sequences) == 2
#         assert "drive" in sequences
#         assert "readout" in sequences

#         drive_str = """
#                 setup:
#                                 wait_sync        4
#                                 set_mrk          0
#                                 upd_param        4

#                 main:
#                                 play             0, 1, 100
#                                 set_mrk          0
#                                 upd_param        4
#                                 stop
#             """
#         assert is_q1asm_equal(sequences["drive"]._program, drive_str)
#         assert is_q1asm_equal(sequences["drive"]._program, sequences_no_block["drive"]._program)

#     def test_play_named_operation_raises_error_if_operations_not_in_calibration(self, play_named_operation: QProgram):
#         calibration = Calibration()
#         compiler = QbloxCompiler()
#         with pytest.raises(RuntimeError):
#             _ = compiler.compile(play_named_operation, bus_mapping={"drive": "drive_q0"}, calibration=calibration)

#     def test_no_loops_all_operations(self, no_loops_all_operations: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=no_loops_all_operations)

#         assert len(sequences) == 2
#         assert "drive" in sequences
#         assert "readout" in sequences

#         for bus in sequences:
#             assert isinstance(sequences[bus], QPy.Sequence)

#         assert len(sequences["drive"]._waveforms._waveforms) == 2
#         assert len(sequences["drive"]._acquisitions._acquisitions) == 0
#         assert len(sequences["drive"]._weights._weights) == 0
#         assert sequences["drive"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             set_freq         1200
#                             set_freq         1200
#                             set_ph           250000000
#                             reset_ph
#                             set_awg_gain     16383, 16383
#                             set_awg_gain     16383, 16383
#                             set_awg_offs     16383, 16383
#                             play             0, 1, 40
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)

#         assert len(sequences["readout"]._waveforms._waveforms) == 4
#         assert len(sequences["readout"]._acquisitions._acquisitions) == 1
#         assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 1
#         assert len(sequences["readout"]._weights._weights) == 2
#         assert sequences["readout"]._program._compiled

#         readout_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             wait             40
#                             wait             100
#                             move             10, R0
#             square_0:
#                             play             0, 1, 100
#                             loop             R0, @square_0
#                             set_mrk          7
#                             play             2, 3, 4
#                             acquire_weighed  0, 0, 0, 1, 2000
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     def test_set_offset_without_path_1_throws_exception(self, caplog, offset_no_path1: QProgram):
#         compiler = QbloxCompiler()
#         with caplog.at_level(logging.WARNING):
#             _ = compiler.compile(qprogram=offset_no_path1)
#         assert (
#             "Qblox requires an offset for the two paths, the offset of the second path has been set to the same as the first path."
#             in caplog.text
#         )

#     def test_dynamic_wait(self, dynamic_wait: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=dynamic_wait)

#         assert len(sequences) == 1
#         assert "drive" in sequences

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             11, R0
#                             move             100, R1
#             loop_0:
#                             play             0, 1, 40
#                             wait             R1
#                             add              R1, 10, R1
#                             loop             R0, @loop_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """

#         assert is_q1asm_equal(sequences["drive"], drive_str)

#     def test_dynamic_wait_multiple_buses_with_disable_autosync(
#         self, dynamic_wait_multiple_buses_with_disable_autosync: QProgram
#     ):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=dynamic_wait_multiple_buses_with_disable_autosync)

#         assert len(sequences) == 2
#         assert "drive" in sequences
#         assert "readout" in sequences

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             11, R0
#                             move             100, R1
#             loop_0:
#                             play             0, 1, 40
#                             add              R1, 10, R1
#                             loop             R0, @loop_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """

#         readout_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             11, R0
#                             move             100, R1
#             loop_0:
#                             wait             R1
#                             play             0, 1, 40
#                             add              R1, 10, R1
#                             loop             R0, @loop_0
#                             nop
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """

#         assert is_q1asm_equal(sequences["drive"], drive_str)
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     def test_dynamic_wait_multiple_buses_throws_exception(self, dynamic_wait_multiple_buses: QProgram):
#         with pytest.raises(NotImplementedError, match="Dynamic syncing is not implemented yet."):
#             compiler = QbloxCompiler()
#             _ = compiler.compile(qprogram=dynamic_wait_multiple_buses)

#     def test_sync_operation_with_dynamic_timings_throws_exception(self, sync_with_dynamic_wait: QProgram):
#         with pytest.raises(NotImplementedError, match="Dynamic syncing is not implemented yet."):
#             compiler = QbloxCompiler()
#             _ = compiler.compile(qprogram=sync_with_dynamic_wait)

#     def test_average_with_long_wait(self, average_loop_long_wait: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=average_loop_long_wait)

#         assert len(sequences) == 2
#         assert "drive" in sequences
#         assert "readout" in sequences

#         for bus in sequences:
#             assert isinstance(sequences[bus], QPy.Sequence)

#         assert len(sequences["drive"]._waveforms._waveforms) == 2
#         assert len(sequences["drive"]._acquisitions._acquisitions) == 0
#         assert len(sequences["drive"]._weights._weights) == 0
#         assert sequences["drive"]._program._compiled

#         assert len(sequences["readout"]._waveforms._waveforms) == 2
#         assert len(sequences["readout"]._acquisitions._acquisitions) == 1
#         assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 1
#         assert len(sequences["readout"]._weights._weights) == 1
#         assert sequences["readout"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4
#             main:
#                             move             1000, R0
#             avg_0:
#                             play             0, 1, 40
#                             wait             65532
#                             wait             34468
#                             wait             2000
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """

#         readout_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             wait             65532
#                             wait             34508
#                             move             10, R1
#             square_0:
#                             play             0, 1, 100
#                             loop             R1, @square_0
#                             acquire_weighed  0, 0, 0, 0, 1000
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     def test_infinite_loop(self, infinite_loop: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=infinite_loop)

#         assert len(sequences) == 1
#         assert "drive" in sequences

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#             infinite_loop_0:
#                             play             0, 1, 40
#                             jmp              @infinite_loop_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """

#         assert is_q1asm_equal(sequences["drive"], drive_str)

#     def test_average_loop(self, average_loop: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=average_loop)

#         assert len(sequences) == 2
#         assert "drive" in sequences
#         assert "readout" in sequences

#         for bus in sequences:
#             assert isinstance(sequences[bus], QPy.Sequence)

#         assert len(sequences["drive"]._waveforms._waveforms) == 2
#         assert len(sequences["drive"]._acquisitions._acquisitions) == 0
#         assert len(sequences["drive"]._weights._weights) == 0
#         assert sequences["drive"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             play             0, 1, 40
#                             wait             2100
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)

#         assert len(sequences["readout"]._waveforms._waveforms) == 2
#         assert len(sequences["readout"]._acquisitions._acquisitions) == 1
#         assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 1
#         assert len(sequences["readout"]._weights._weights) == 1
#         assert sequences["readout"]._program._compiled

#         readout_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             wait             40
#                             wait             100
#                             move             10, R1
#             square_0:
#                             play             0, 1, 100
#                             loop             R1, @square_0
#                             acquire_weighed  0, 0, 0, 0, 1000
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     def test_average_with_for_loop_variable_does_nothing(self, average_with_for_loop_nshots: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=average_with_for_loop_nshots)

#         assert len(sequences) == 2
#         assert "drive" in sequences
#         assert "readout" in sequences

#         for bus in sequences:
#             assert isinstance(sequences[bus], QPy.Sequence)

#         assert len(sequences["drive"]._waveforms._waveforms) == 2
#         assert len(sequences["drive"]._acquisitions._acquisitions) == 0
#         assert len(sequences["drive"]._weights._weights) == 0
#         assert sequences["drive"]._program._compiled

#         assert len(sequences["readout"]._waveforms._waveforms) == 2
#         assert len(sequences["readout"]._acquisitions._acquisitions) == 1
#         assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 3
#         assert len(sequences["readout"]._weights._weights) == 2
#         assert sequences["readout"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             3, R1
#                             move             0, R2
#             loop_0:
#                             play             0, 1, 40
#                             wait             2960
#                             add              R2, 1, R2
#                             loop             R1, @loop_0
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         readout_str = """
#             setup:
#                 wait_sync        4
#                 set_mrk          0
#                 upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             1, R1
#                             move             0, R2
#                             move             0, R3
#                             move             3, R4
#                             move             0, R5
#             loop_0:
#                             move             10, R6
#             square_0:
#                             play             0, 1, 100
#                             loop             R6, @square_0
#                             acquire_weighed  0, R3, R2, R1, 2000
#                             add              R3, 1, R3
#                             add              R5, 1, R5
#                             loop             R4, @loop_0
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     def test_average_with_for_loop(self, average_with_for_loop: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=average_with_for_loop)

#         assert len(sequences) == 2
#         assert "drive" in sequences
#         assert "readout" in sequences

#         for bus in sequences:
#             assert isinstance(sequences[bus], QPy.Sequence)

#         assert len(sequences["drive"]._waveforms._waveforms) == 2
#         assert len(sequences["drive"]._acquisitions._acquisitions) == 0
#         assert len(sequences["drive"]._weights._weights) == 0
#         assert sequences["drive"]._program._compiled

#         assert len(sequences["readout"]._waveforms._waveforms) == 2
#         assert len(sequences["readout"]._acquisitions._acquisitions) == 1
#         assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 11
#         assert len(sequences["readout"]._weights._weights) == 2
#         assert sequences["readout"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             11, R1
#                             move             0, R2
#             loop_0:
#                             play             0, 1, 40
#                             wait             2960
#                             add              R2, 3276, R2
#                             loop             R1, @loop_0
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         readout_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             1, R1
#                             move             0, R2
#                             move             0, R3
#                             move             11, R4
#                             move             0, R5
#             loop_0:
#                             set_awg_gain     R5, R5
#                             set_awg_gain     R5, R5
#                             move             10, R6
#             square_0:
#                             play             0, 1, 100
#                             loop             R6, @square_0
#                             acquire_weighed  0, R3, R2, R1, 2000
#                             add              R3, 1, R3
#                             add              R5, 3276, R5
#                             loop             R4, @loop_0
#                             nop
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     def test_average_with_linspace(self, average_with_linspace: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=average_with_linspace)

#         assert len(sequences) == 2
#         assert "drive" in sequences
#         assert "readout" in sequences

#         for bus in sequences:
#             assert isinstance(sequences[bus], QPy.Sequence)

#         assert len(sequences["drive"]._waveforms._waveforms) == 2
#         assert len(sequences["drive"]._acquisitions._acquisitions) == 0
#         assert len(sequences["drive"]._weights._weights) == 0
#         assert sequences["drive"]._program._compiled

#         assert len(sequences["readout"]._waveforms._waveforms) == 2
#         assert len(sequences["readout"]._acquisitions._acquisitions) == 1
#         assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 11
#         assert len(sequences["readout"]._weights._weights) == 2
#         assert sequences["readout"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             11, R1
#                             move             0, R2
#             loop_0:
#                             play             0, 1, 40
#                             wait             2960
#                             add              R2, 3276, R2
#                             loop             R1, @loop_0
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         readout_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             1, R1
#                             move             0, R2
#                             move             0, R3
#                             move             11, R4
#                             move             0, R5
#             loop_0:
#                             set_awg_gain     R5, R5
#                             set_awg_gain     R5, R5
#                             move             10, R6
#             square_0:
#                             play             0, 1, 100
#                             loop             R6, @square_0
#                             acquire_weighed  0, R3, R2, R1, 2000
#                             add              R3, 1, R3
#                             add              R5, 3276, R5
#                             loop             R4, @loop_0
#                             nop
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     def test_measure_calls_play_acquire(self, measure_program):
#         compiler = QbloxCompiler()

#         # Test measure with default time of flight
#         with (
#             patch.object(QbloxCompiler, "_handle_play") as handle_play,
#             patch.object(QbloxCompiler, "_handle_acquire") as handle_acquire,
#         ):
#             compiler.compile(measure_program)

#             measure = measure_program.body.elements[0]
#             assert handle_play.call_count == 1
#             assert handle_acquire.call_count == 1
#             assert handle_play.call_args[0][0].bus == measure.bus
#             assert handle_play.call_args[0][0].waveform == measure.waveform
#             assert handle_play.call_args[0][0].wait_time == QbloxCompiler.minimum_wait_duration
#             assert handle_acquire.call_args[0][0].bus == measure.bus
#             assert handle_acquire.call_args[0][0].weights == measure.weights

#         # Test measure with provided time of flight
#         with (
#             patch.object(QbloxCompiler, "_handle_play") as handle_play,
#             patch.object(QbloxCompiler, "_handle_acquire") as handle_acquire,
#         ):
#             compiler.compile(measure_program, times_of_flight={"readout": 123})

#             measure = measure_program.body.elements[0]
#             assert handle_play.call_count == 1
#             assert handle_acquire.call_count == 1
#             assert handle_play.call_args[0][0].bus == measure.bus
#             assert handle_play.call_args[0][0].waveform == measure.waveform
#             assert handle_play.call_args[0][0].wait_time == 123
#             assert handle_acquire.call_args[0][0].bus == measure.bus
#             assert handle_acquire.call_args[0][0].weights == measure.weights

#     def test_acquire_loop_with_for_loop_with_weights_of_same_waveform(
#         self, acquire_loop_with_for_loop_with_weights_of_same_waveform: QProgram
#     ):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=acquire_loop_with_for_loop_with_weights_of_same_waveform)

#         assert len(sequences) == 2
#         assert "drive" in sequences
#         assert "readout" in sequences

#         for bus in sequences:
#             assert isinstance(sequences[bus], QPy.Sequence)

#         assert len(sequences["drive"]._waveforms._waveforms) == 2
#         assert len(sequences["drive"]._acquisitions._acquisitions) == 0
#         assert len(sequences["drive"]._weights._weights) == 0
#         assert sequences["drive"]._program._compiled

#         assert len(sequences["readout"]._waveforms._waveforms) == 2
#         assert len(sequences["readout"]._acquisitions._acquisitions) == 1
#         assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 11
#         assert len(sequences["readout"]._weights._weights) == 1
#         assert sequences["readout"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             11, R1
#                             move             0, R2
#             loop_0:
#                             play             0, 1, 40
#                             wait             1960
#                             add              R2, 3276, R2
#                             loop             R1, @loop_0
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         readout_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             0, R1
#                             move             0, R2
#                             move             0, R3
#                             move             11, R4
#                             move             0, R5
#             loop_0:
#                             set_awg_gain     R5, R5
#                             set_awg_gain     R5, R5
#                             move             10, R6
#             square_0:
#                             play             0, 1, 100
#                             loop             R6, @square_0
#                             acquire_weighed  0, R3, R2, R1, 1000
#                             add              R3, 1, R3
#                             add              R5, 3276, R5
#                             loop             R4, @loop_0
#                             nop
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     def test_average_with_multiple_for_loops_and_acquires(self, average_with_multiple_for_loops_and_acquires: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=average_with_multiple_for_loops_and_acquires)

#         assert len(sequences) == 1
#         assert "readout" in sequences

#         for bus in sequences:
#             assert isinstance(sequences[bus], QPy.Sequence)

#         assert len(sequences["readout"]._waveforms._waveforms) == 2
#         assert len(sequences["readout"]._acquisitions._acquisitions) == 3
#         assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 51
#         assert sequences["readout"]._acquisitions._acquisitions[1].num_bins == 1
#         assert sequences["readout"]._acquisitions._acquisitions[2].num_bins == 11
#         assert len(sequences["readout"]._weights._weights) == 6
#         assert sequences["readout"]._program._compiled

#         readout_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             5, R1
#                             move             4, R2
#                             move             0, R3
#                             move             1, R4
#                             move             0, R5
#                             move             0, R6
#                             move             51, R7
#                             move             0, R8
#             loop_0:
#                             set_freq         R8
#                             set_freq         R8
#                             move             10, R9
#             square_0:
#                             play             0, 1, 100
#                             loop             R9, @square_0
#                             acquire_weighed  0, R6, R5, R4, 2000
#                             add              R6, 1, R6
#                             add              R8, 40, R8
#                             loop             R7, @loop_0
#                             nop
#                             acquire_weighed  1, 0, 2, 3, 1000
#                             move             11, R10
#                             move             0, R11
#                             nop
#             loop_1:
#                             set_awg_gain     R11, R11
#                             set_awg_gain     R11, R11
#                             move             10, R12
#             square_1:
#                             play             0, 1, 100
#                             loop             R12, @square_1
#                             acquire_weighed  2, R3, R2, R1, 500
#                             add              R3, 1, R3
#                             add              R11, 3276, R11
#                             loop             R10, @loop_1
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     def test_average_with_nested_for_loops(self, average_with_nested_for_loops: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=average_with_nested_for_loops)

#         assert len(sequences) == 2
#         assert "drive" in sequences
#         assert "readout" in sequences

#         for bus in sequences:
#             assert isinstance(sequences[bus], QPy.Sequence)

#         assert len(sequences["drive"]._waveforms._waveforms) == 2
#         assert len(sequences["drive"]._acquisitions._acquisitions) == 0
#         assert len(sequences["drive"]._weights._weights) == 0
#         assert sequences["drive"]._program._compiled

#         assert len(sequences["readout"]._waveforms._waveforms) == 2
#         assert len(sequences["readout"]._acquisitions._acquisitions) == 1
#         assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 561
#         assert len(sequences["readout"]._weights._weights) == 2
#         assert sequences["readout"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             11, R1
#                             move             0, R2
#             loop_0:
#                             set_awg_gain     R2, R2
#                             set_awg_gain     R2, R2
#                             move             51, R3
#                             move             0, R4
#             loop_1:
#                             play             0, 1, 40
#                             wait             3000
#                             add              R4, 40, R4
#                             loop             R3, @loop_1
#                             add              R2, 3276, R2
#                             loop             R1, @loop_0
#                             nop
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         readout_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             1, R1
#                             move             0, R2
#                             move             0, R3
#                             move             11, R4
#                             move             0, R5
#             loop_0:
#                             move             51, R6
#                             move             0, R7
#             loop_1:
#                             wait             40
#                             set_freq         R7
#                             set_freq         R7
#                             move             10, R8
#             square_0:
#                             play             0, 1, 100
#                             loop             R8, @square_0
#                             acquire_weighed  0, R3, R2, R1, 2000
#                             add              R3, 1, R3
#                             add              R7, 40, R7
#                             loop             R6, @loop_1
#                             add              R5, 3276, R5
#                             loop             R4, @loop_0
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     def test_average_with_parallel_for_loops(self, average_with_parallel_for_loops: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=average_with_parallel_for_loops)

#         assert len(sequences) == 2
#         assert "drive" in sequences
#         assert "readout" in sequences

#         for bus in sequences:
#             assert isinstance(sequences[bus], QPy.Sequence)

#         assert len(sequences["drive"]._waveforms._waveforms) == 2
#         assert len(sequences["drive"]._acquisitions._acquisitions) == 0
#         assert len(sequences["drive"]._weights._weights) == 0
#         assert sequences["drive"]._program._compiled

#         assert len(sequences["readout"]._waveforms._waveforms) == 2
#         assert len(sequences["readout"]._acquisitions._acquisitions) == 1
#         assert sequences["readout"]._acquisitions._acquisitions[0].num_bins == 11
#         assert len(sequences["readout"]._weights._weights) == 2
#         assert sequences["readout"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             11, R1
#                             move             400, R2
#                             move             0, R3
#             loop_0:
#                             set_awg_gain     R3, R3
#                             set_awg_gain     R3, R3
#                             play             0, 1, 40
#                             wait             3000
#                             add              R2, 40, R2
#                             add              R3, 3276, R3
#                             loop             R1, @loop_0
#                             nop
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         readout_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             1, R1
#                             move             0, R2
#                             move             0, R3
#                             move             11, R4
#                             move             400, R5
#                             move             0, R6
#             loop_0:
#                             set_freq         R5
# set_freq         R5
#                             upd_param        4
#                             wait             36
#                             move             10, R7
#             square_0:
#                             play             0, 1, 100
#                             loop             R7, @square_0
#                             acquire_weighed  0, R3, R2, R1, 2000
#                             add              R3, 1, R3
#                             add              R5, 40, R5
#                             add              R6, 3276, R6
#                             loop             R4, @loop_0
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     def test_multiple_play_operations_with_same_waveform(self, multiple_play_operations_with_same_waveform: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=multiple_play_operations_with_same_waveform)

#         assert len(sequences) == 1
#         assert "drive" in sequences

#         for bus in sequences:
#             assert isinstance(sequences[bus], QPy.Sequence)

#         assert len(sequences["drive"]._waveforms._waveforms) == 2
#         assert len(sequences["drive"]._acquisitions._acquisitions) == 0
#         assert len(sequences["drive"]._weights._weights) == 0
#         assert sequences["drive"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             play             0, 1, 40
#                             play             0, 1, 40
#                             play             0, 1, 40
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)

#     def test_multiple_play_operations_with_no_Q_waveform(self, multiple_play_operations_with_no_Q_waveform: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=multiple_play_operations_with_no_Q_waveform)

#         assert len(sequences) == 1
#         assert "drive" in sequences

#         for bus in sequences:
#             assert isinstance(sequences[bus], QPy.Sequence)

#         assert len(sequences["drive"]._waveforms._waveforms) == 2
#         assert len(sequences["drive"]._acquisitions._acquisitions) == 0
#         assert len(sequences["drive"]._weights._weights) == 0
#         assert sequences["drive"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             play             0, 1, 40
#                             play             0, 1, 40
#                             play             0, 1, 40
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)

#     def test_play_square_waveforms_with_optimization(self, play_square_waveforms_with_optimization: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=play_square_waveforms_with_optimization)

#         assert len(sequences["drive"]._waveforms._waveforms) == 11
#         assert sequences["drive"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             play             0, 1, 25
#                             play             2, 3, 50
#                             move             5, R0
#             square_0:
#                             play             4, 5, 100
#                             loop             R0, @square_0
#                             move             5, R1
#             square_1:
#                             play             4, 6, 100
#                             loop             R1, @square_1
#                             move             500, R2
#             square_2:
#                             play             4, 5, 100
#                             loop             R2, @square_2
#                             move             97902, R3
#             square_3:
#                             play             4, 5, 100
#                             loop             R3, @square_3
#                             play             7, 8, 23
#                             move             97902, R4
#             square_4:
#                             play             4, 4, 100
#                             loop             R4, @square_4
#                             play             7, 7, 23
#                             move             9721, R5
#             square_5:
#                             play             9, 10, 127
#                             loop             R5, @square_5
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)

#     def test_play_operation_with_variable_in_waveform(self, caplog, play_operation_with_variable_in_waveform: QProgram):
#         compiler = QbloxCompiler()
#         with caplog.at_level(logging.ERROR):
#             _ = compiler.compile(qprogram=play_operation_with_variable_in_waveform)

#         assert "Variables in waveforms are not supported in Qblox." in caplog.text

#     def test_delay(self, average_with_for_loop_nshots: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=average_with_for_loop_nshots, delays={"drive": 20})

#         assert len(sequences) == 2
#         assert "drive" in sequences
#         assert "readout" in sequences

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             3, R1
#                             move             0, R2
#             loop_0:
#                             wait             20
#                             play             0, 1, 40
#                             wait             2960
#                             add              R2, 1, R2
#                             loop             R1, @loop_0
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         readout_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             1, R1
#                             move             0, R2
#                             move             0, R3
#                             move             3, R4
#                             move             0, R5
#             loop_0:
#                             move             10, R6
#             square_0:
#                             play             0, 1, 100
#                             loop             R6, @square_0
#                             acquire_weighed  0, R3, R2, R1, 2000
#                             add              R3, 1, R3
#                             wait             20
#                             add              R5, 1, R5
#                             loop             R4, @loop_0
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     def test_negative_delay(self, average_with_for_loop_nshots: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=average_with_for_loop_nshots, delays={"drive": -20})

#         assert len(sequences) == 2
#         assert "drive" in sequences
#         assert "readout" in sequences

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             3, R1
#                             move             0, R2
#             loop_0:
#                             play             0, 1, 40
#                             wait             2980
#                             add              R2, 1, R2
#                             loop             R1, @loop_0
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         readout_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             move             1000, R0
#             avg_0:
#                             move             1, R1
#                             move             0, R2
#                             move             0, R3
#                             move             3, R4
#                             move             0, R5
#             loop_0:
#                             wait             20
#                             move             10, R6
#             square_0:
#                             play             0, 1, 100
#                             loop             R6, @square_0
#                             acquire_weighed  0, R3, R2, R1, 2000
#                             add              R3, 1, R3
#                             add              R5, 1, R5
#                             loop             R4, @loop_0
#                             loop             R0, @avg_0
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """
#         assert is_q1asm_equal(sequences["drive"], drive_str)
#         assert is_q1asm_equal(sequences["readout"], readout_str)

#     @pytest.mark.parametrize(
#         "start,stop,step,expected_result",
#         [(0, 10, 1, 11), (10, 0, -1, 11), (1, 2.05, 0.1, 11)],
#     )
#     def test_calculate_iterations(self, start, stop, step, expected_result):
#         result = QbloxCompiler._calculate_iterations(start, stop, step)
#         assert result == expected_result

#     def test_calculate_iterations_with_zero_step_throws_error(self):
#         with pytest.raises(ValueError, match="Step value cannot be zero"):
#             QbloxCompiler._calculate_iterations(100, 200, 0)

#     def test_update_latched_param_before_wait(self, update_latched_param: QProgram):
#         compiler = QbloxCompiler()
#         sequences, _ = compiler.compile(qprogram=update_latched_param)

#         assert len(sequences) == 1
#         assert "drive" in sequences

#         for bus in sequences:
#             assert isinstance(sequences[bus], QPy.Sequence)

#         assert len(sequences["drive"]._waveforms._waveforms) == 4
#         assert len(sequences["drive"]._acquisitions._acquisitions) == 0
#         assert len(sequences["drive"]._weights._weights) == 0
#         assert sequences["drive"]._program._compiled

#         drive_str = """
#             setup:
#                             wait_sync        4
#                             set_mrk          0
#                             upd_param        4

#             main:
#                             set_awg_offs     32767, 0
#                             upd_param        4
#                             move             1, R0
#             square_0:
#                             play             0, 1, 100
#                             loop             R0, @square_0
#                             set_ph           159154943
#                             upd_param        4
#                             move             1, R1
#             square_1:
#                             play             0, 1, 100
#                             loop             R1, @square_1
#                             set_awg_gain     32767, 32767
#                             set_awg_gain     32767, 32767
#                             upd_param        4
#                             wait             96
#                             play             2, 3, 5
#                             set_freq         4000000
#                             set_freq         4000000
#                             upd_param        4
#                             wait             65532
#                             wait             34464
#                             play             2, 3, 5
#                             set_awg_gain     32767, 32767
#                             set_awg_gain     32767, 32767
#                             upd_param        4
#                             play             2, 3, 5
#                             set_awg_offs     32767, 0
#                             upd_param        6
#                             set_mrk          0
#                             upd_param        4
#                             stop
#         """

#         assert is_q1asm_equal(sequences["drive"], drive_str)
