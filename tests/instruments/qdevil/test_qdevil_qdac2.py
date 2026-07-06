import re
from itertools import product
from unittest.mock import MagicMock, call

import pytest

from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.qdevil.qdevil_qdac2 import QDevilQDac2
from qililab.typings.enums import Parameter
from qililab.waveforms import Square


def _stateful_qdac_device() -> MagicMock:
    """MagicMock emulating the QDAC-II marker registers.

    qililab discovers busy internal triggers with one compound SCPI query per
    channel (`SOUR<n>:<gen>:MARK:<loc>?;:...` via `device.ask`), so the mock
    must remember what was written via `write_channel` and report it back.
    SCPI is case-insensitive and allows abbreviations ("star" == "STARt"),
    hence the per-segment prefix matching. `device.channel` returns a single
    shared mock, so the channel number in the first segment is normalized away.
    """
    device = MagicMock()
    markers: dict[tuple[str, ...], int] = {}

    def _segments(header: str) -> tuple[str, ...]:
        parts = header.upper().rstrip("?").split(":")
        if parts[0].startswith("SOUR"):
            parts[0] = "SOUR"  # SOUR{0} and SOUR<n> address the same shared channel mock
        return tuple(parts)

    def _find(segments):
        for stored in markers:
            if len(stored) == len(segments) and all(
                a.startswith(b) or b.startswith(a) for a, b in zip(stored, segments)
            ):
                return stored
        return None

    def _write_channel(command: str) -> None:
        header, _, value = command.partition(" ")
        segments = _segments(header)
        key = _find(segments) or segments
        markers[key] = int(value)

    def _ask(command: str) -> str:
        values = []
        for sub_query in command.split(";"):
            key = _find(_segments(sub_query.lstrip(":")))
            values.append(str(markers[key] if key else 0))
        return ";".join(values)

    device.ask.side_effect = _ask
    device.channel.return_value.write_channel.side_effect = _write_channel
    return device


def _shared_physical_qdac(n_connections: int = 2):
    """N driver connections to ONE physical QDAC-II.

    Channel objects and marker registers are shared across connections,
    keyed per channel, so trigger allocation on one connection is visible
    to the others via the compound `device.ask` scan — just like real hardware.
    """
    markers: dict[tuple[int, tuple[str, ...]], int] = {}
    channels: dict[int, MagicMock] = {}

    def _segments(header: str) -> tuple[str, ...]:
        parts = header.upper().rstrip("?").split(":")
        parts[0] = "SOUR"  # channel number is carried separately, as the key's first element
        return tuple(parts)

    def _find(cid: int, segments: tuple[str, ...]):
        for key in markers:
            stored_cid, stored = key
            if stored_cid == cid and len(stored) == len(segments) and all(
                a.startswith(b) or b.startswith(a) for a, b in zip(stored, segments)
            ):
                return key
        return None

    def _get_channel(channel_id) -> MagicMock:
        cid = int(channel_id)
        if cid not in channels:
            ch = MagicMock()

            def _write(command: str, _cid=cid) -> None:
                header, _, value = command.partition(" ")
                key = _find(_cid, _segments(header)) or (_cid, _segments(header))
                markers[key] = int(value)

            ch.write_channel.side_effect = _write
            channels[cid] = ch
        return channels[cid]

    def _ask(command: str) -> str:
        values = []
        for sub_query in command.split(";"):
            header = sub_query.lstrip(":")
            cid = int(header.split(":", 1)[0].upper().removeprefix("SOUR"))
            key = _find(cid, _segments(header))
            values.append(str(markers[key] if key else 0))
        return ";".join(values)

    devices = []
    for _ in range(n_connections):
        device = MagicMock()
        device.name = "qdac_shared"  # one physical instrument, one name
        device.channel.side_effect = _get_channel
        device.ask.side_effect = _ask
        devices.append(device)
    return devices, channels


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
            "dacs": [2, 4, 10, 11],
            "low_pass_filter": ["dc", "dc", "dc", "dc"],
        }
    )
    qdac.device = _stateful_qdac_device()
    return qdac


@pytest.fixture(name="qdac_2")
def fixture_qdac_2() -> QDevilQDac2:
    """Fixture that returns an instance of a dummy QDAC-II."""
    qdac = QDevilQDac2(
        {
            "alias": "qdac_2",
            "voltage": [0.5, 0.5, 0.5, 0.5],
            "span": ["low", "low", "low", "low"],
            "ramping_enabled": [True, True, True, False],
            "ramp_rate": [0.01, 0.01, 0.01, 0.01],
            "dacs": [1, 3, 9, 12],
            "low_pass_filter": ["dc", "dc", "dc", "dc"],
        }
    )
    qdac.device = _stateful_qdac_device()
    return qdac


@pytest.fixture(name="qdac_out_range")
def range_input() -> QDevilQDac2:
    """Fixture that returns an instance of a dummy QDAC-II."""

    qdac_out_range = QDevilQDac2(
        {
            "alias": "qdac_out_range",
            "voltage": [0.5],
            "span": ["low"],
            "ramping_enabled": [True],
            "ramp_rate": [0.001],
            "dacs": [10],
            "low_pass_filter": ["dc"],
        }
    )
    mock_device = MagicMock()
    qdac_out_range.device = mock_device
    return qdac_out_range


@pytest.fixture(name="waveform")
def get_square_waveform() -> Square:
    return Square(0.1, 4)


class TestQDevilQDac2:
    def test_initial_setup(self, qdac: QDevilQDac2):
        """Test initial_setup method"""
        qdac.initial_setup()

        channel_calls = []
        for channel_id in qdac.dacs:
            index = qdac.dacs.index(channel_id)
            channel_calls.append(call(channel_id))
            channel_calls.append(call().dc_mode("fixed"))
            channel_calls.append(call().output_range(qdac.span[index]))
            channel_calls.append(call().output_filter(qdac.low_pass_filter[index]))
            if qdac.ramping_enabled[index]:
                channel_calls.append(call().dc_slew_rate_V_per_s(qdac.ramp_rate[index]))
            else:
                channel_calls.append(call().dc_slew_rate_V_per_s(2e7))
            channel_calls.append(call().dc_constant_V(0.0))

        qdac.device.channel.assert_has_calls(channel_calls)

    def test_turn_on(self, qdac: QDevilQDac2):
        """Test turn_on method"""
        qdac.turn_on()

        channel_calls = []
        for channel_id in qdac.dacs:
            index = qdac.dacs.index(channel_id)
            channel_calls.append(call(channel_id))
            channel_calls.append(call().dc_constant_V(qdac.voltage[index]))

        qdac.device.channel.assert_has_calls(channel_calls)

    def test_turn_off(self, qdac: QDevilQDac2, waveform: Square):
        """Test turn_off method"""
        # Create test trigger dictionary
        channel_id = 4
        out_port = 1
        trigger = "trigger_test"
        qdac._triggers = {}
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.set_start_marker_external_trigger(channel_id, out_port, trigger)

        qdac.turn_off()

        channel_calls = []
        for channel_id in qdac.dacs:
            channel_calls.append(call(channel_id))
            channel_calls.append(call().dc_constant_V(0.0))

        qdac.device.channel.assert_has_calls(channel_calls)

    def test_reset(self, qdac: QDevilQDac2, waveform: Square):
        """Test reset method"""
        # Create test trigger dictionary
        channel_id = 4
        out_port = 1
        trigger = "trigger_test"
        qdac._triggers = {}
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.set_start_marker_external_trigger(channel_id, out_port, trigger)

        qdac.reset()

        qdac.device.reset.assert_called_once()
        assert qdac._triggers == {}          # trigger was actually freed
        assert qdac._cache_awg == {}
        assert qdac._cache_dc == {}
        # reset released the marker on the instrument
        qdac.device.channel.return_value.write_channel.assert_any_call("SOUR{0}:DC:MARK:PSTart 0")

    def test_get_dac(self, qdac: QDevilQDac2):
        """Test get_dac method"""
        channel_calls = []
        for channel_id in qdac.dacs:
            qdac.get_dac(channel_id)
            channel_calls.append(call(channel_id))
        qdac.device.channel.assert_has_calls(channel_calls)

    def test_upload_awg_waveform(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        qdac.upload_awg_waveform(waveform, channel_id)
        qdac.device.allocate_trace.assert_called_once_with(channel_id, len(waveform.envelope()))
        assert qdac._cache_awg == {channel_id: qdac.device.allocate_trace.return_value}
        # the waveform data was actually pushed to the trace
        qdac.device.allocate_trace.return_value.waveform.assert_called_once_with(list(waveform.envelope()))

    def test_upload_awg_waveform_fails_overwrite_cache(self, qdac: QDevilQDac2, waveform: Square):
        """Test that upload waveform raises an error when trying to allocate a waveform to an already allocated channel id"""
        channel_id = 2
        qdac._cache_awg = {channel_id: True}
        error_string = re.escape(
            f"Device {qdac.name} already has a waveform allocated to channel {channel_id}. Clear the cache before allocating a new waveform"
        )
        with pytest.raises(ValueError, match=error_string):
            qdac.upload_awg_waveform(waveform, channel_id)

    def test_upload_awg_waveform_fails_odd_value(self, qdac: QDevilQDac2):
        """Test that upload waveform raises an error when uploading a waveform with odd number of entries"""
        channel_id = 2
        waveform = Square(0.1, 3)
        error_string = "Waveform entries must be even."
        with pytest.raises(ValueError, match=error_string):
            qdac.upload_awg_waveform(waveform, channel_id)

    def test_upload_awg_waveform_fails_amp_range(self, qdac: QDevilQDac2):
        """Test that upload waveform raises an error when uploading a waveform with outside the allowed amplitude range"""
        channel_id = 2
        waveform = Square(1, 4)
        error_string = re.escape("Waveform amplitudes must be within [-1,1] range.")
        with pytest.raises(ValueError, match=error_string):
            qdac.upload_awg_waveform(waveform, channel_id)
        qdac.clear_cache()
        channel_id = 2
        waveform = Square(-1.1, 4)
        with pytest.raises(ValueError, match=error_string):
            qdac.upload_awg_waveform(waveform, channel_id)

    def test_play_awg(self, qdac: QDevilQDac2):
        """Test play method"""
        channel_id = 4
        channel_calls = [call(4), call().start(), call(4), call().start()]
        qdac._cache_awg = {channel_id: True}
        qdac.play_awg(channel_id, clear_after=False)
        # cache not erased if default clear_after
        assert qdac._cache_awg == {channel_id: True}

        qdac.play_awg(channel_id)
        qdac.get_dac(4).arbitrary_wave.assert_has_calls(channel_calls)
        # check that cache is erased
        assert qdac._cache_awg == {}

        qdac.play_awg()
        qdac.device.start_all.assert_called_once()

    def test_upload_voltage_list(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        qdac._cache_dc = {}
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.device.channel(channel_id).dc_list.assert_called_once()
        waveform = Square(0.1, 3)
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.device.remove_traces.assert_called_once()
        qdac.device.channel(channel_id).dc_list.assert_called()

    def test_upload_voltage_list_raises_channel_error(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 5
        with pytest.raises(
            ValueError,
            match=f"The specified `channel_id`: {channel_id} is not added to the QDAC-II instrument controller dac list.",
        ):
            qdac.upload_voltage_list(waveform, channel_id)

    def test_set_in_external_trigger(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        in_port = 1
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.set_in_external_trigger(channel_id, in_port)

        qdac._cache_dc[f"{qdac.device.name}_{channel_id}"].start_on_external.assert_called_once()

    def test_set_in_external_trigger_no_cache_raises_error(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        in_port = 1
        qdac._cache_dc = {}

        with pytest.raises(
            ValueError,
            match=f"No DC list with the given channel ID, first create a DC list with channel ID: {channel_id}",
        ):
            qdac.set_in_external_trigger(channel_id, in_port)

    def test_set_out_external_trigger(self, qdac: QDevilQDac2, waveform: Square):
        """Test set_out_external_trigger method"""
        channel_id = 4
        out_port = 1
        trigger = "trigger_test"
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.set_out_external_trigger(channel_id, out_port, trigger)
        qdac.device.connect_external_trigger.assert_called_once()

        # Second call clears the old trigger before re-allocating
        qdac.set_out_external_trigger(channel_id, out_port, trigger)
        qdac.device.channel.return_value.write_channel.assert_any_call("SOUR{0}:DC:MARK:STARt 0")
        assert qdac.device.connect_external_trigger.call_count == 2

    def test_set_out_external_trigger_no_cache_raises_error(self, qdac: QDevilQDac2, waveform: Square):
        """Test set_out_external_trigger method raises error when no DC list is created"""
        channel_id = 4
        out_port = 1
        trigger = "trigger_test"
        qdac._cache_dc = {}

        with pytest.raises(
            ValueError,
            match=f"No DC list with the given channel ID, first create a DC list with channel ID: {channel_id}",
        ):
            qdac.set_out_external_trigger(channel_id, out_port, trigger)

    def test_set_out_internal_trigger(self, qdac: QDevilQDac2, waveform: Square):
        """Test set_out_internal_trigger method"""
        channel_id = 4
        trigger = "trigger_test"
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.set_out_internal_trigger(channel_id, trigger)
        assert qdac._triggers[trigger].value == 1

        # Second call clears the old trigger before re-allocating
        qdac.set_out_internal_trigger(channel_id, trigger)
        qdac.device.channel.return_value.write_channel.assert_any_call("SOUR{0}:DC:MARK:STARt 0")

    def test_set_out_internal_trigger_no_cache_raises_error(self, qdac: QDevilQDac2, waveform: Square):
        """Test set_out_internal_trigger method raises error when no DC list is created"""
        channel_id = 4
        trigger = "trigger_test"
        qdac._cache_dc = {}

        with pytest.raises(
            ValueError,
            match=f"No DC list with the given channel ID, first create a DC list with channel ID: {channel_id}",
        ):
            qdac.set_out_internal_trigger(channel_id, trigger)

    def test_set_end_marker_external_trigger(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id, out_port, trigger = 4, 1, "trigger_test"
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.set_end_marker_external_trigger(channel_id, out_port, trigger)
        qdac.device.connect_external_trigger.assert_called_once()

        qdac.set_end_marker_external_trigger(channel_id, out_port, trigger, step=True)
        qdac.device.channel.return_value.write_channel.assert_any_call("SOUR{0}:DC:MARK:PEND 0")
        assert qdac.device.connect_external_trigger.call_count == 2

    def test_set_end_marker_external_trigger_stepped(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        out_port = 1
        trigger = "trigger_test"
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.set_end_marker_external_trigger(channel_id, out_port, trigger, step=True)
        qdac.device.connect_external_trigger.assert_called_once()
        qdac.device.channel.return_value.write_channel.assert_any_call(
            f"SOUR{{0}}:DC:MARK:SEND {qdac._triggers[trigger].value}"
        )

    def test_set_end_marker_external_trigger_no_cache_raises_error(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        out_port = 1
        trigger = "trigger_test"
        qdac._cache_dc = {}

        with pytest.raises(
            ValueError,
            match=f"No DC list with the given channel ID, first create a DC list with channel ID: {channel_id}",
        ):
            qdac.set_end_marker_external_trigger(channel_id, out_port, trigger)

    def test_set_start_marker_external_trigger(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        out_port = 1
        trigger = "trigger_test"
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.set_start_marker_external_trigger(channel_id, out_port, trigger)
        qdac.device.connect_external_trigger.assert_called_once()

        # step=True re-call: old PSTart marker is released, SSTart is set
        qdac.set_start_marker_external_trigger(channel_id, out_port, trigger, step=True)
        qdac.device.channel.return_value.write_channel.assert_any_call("SOUR{0}:DC:MARK:PSTart 0")
        assert qdac.device.connect_external_trigger.call_count == 2

    def test_set_start_marker_external_trigger_no_cache_raises_error(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        out_port = 1
        trigger = "trigger_test"
        qdac._cache_dc = {}

        with pytest.raises(
            ValueError,
            match=f"No DC list with the given channel ID, first create a DC list with channel ID: {channel_id}",
        ):
            qdac.set_start_marker_external_trigger(channel_id, out_port, trigger)

    def test_set_end_marker_internal_trigger(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        trigger = "trigger_test"
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.set_end_marker_internal_trigger(channel_id, trigger)
        qdac.device.channel.return_value.write_channel.assert_called_once()

        qdac.set_end_marker_internal_trigger(channel_id, trigger, step=True)
        qdac.device.channel.return_value.write_channel.assert_any_call("SOUR{0}:DC:MARK:PEND 0")

    def test_set_end_marker_internal_trigger_no_cache_raises_error(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        trigger = "trigger_test"
        qdac._cache_dc = {}

        with pytest.raises(
            ValueError,
            match=f"No DC list with the given channel ID, first create a DC list with channel ID: {channel_id}",
        ):
            qdac.set_end_marker_internal_trigger(channel_id, trigger)

    def test_set_start_marker_internal_trigger(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        trigger = "trigger_test"
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.set_start_marker_internal_trigger(channel_id, trigger)
        qdac.device.channel.return_value.write_channel.assert_called_once()

        qdac.set_start_marker_internal_trigger(channel_id, trigger, step=True)
        qdac.device.channel.return_value.write_channel.assert_any_call("SOUR{0}:DC:MARK:PSTart 0")

    def test_set_start_marker_internal_trigger_no_cache_raises_error(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        trigger = "trigger_test"
        qdac._cache_dc = {}

        with pytest.raises(
            ValueError,
            match=f"No DC list with the given channel ID, first create a DC list with channel ID: {channel_id}",
        ):
            qdac.set_start_marker_internal_trigger(channel_id, trigger)

    def test_set_in_internal_trigger(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        trigger = "trigger_test"
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.set_start_marker_internal_trigger(channel_id, trigger)
        qdac.set_in_internal_trigger(channel_id, trigger)

        qdac._cache_dc[f"{qdac.device.name}_{channel_id}"].start_on.assert_called_once()

    def test_set_in_internal_trigger_no_trigger_raises_error(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        trigger = "trigger_test"
        qdac._triggers = {}

        with pytest.raises(
            ValueError,
            match=f"Trigger with name {trigger} not created.",
        ):
            qdac.set_in_internal_trigger(channel_id, trigger)

    def test_set_in_internal_trigger_no_cache_raises_error(self, qdac: QDevilQDac2, waveform: Square):
        """Test upload_waveform method"""
        channel_id = 4
        trigger = "trigger_test"
        qdac._cache_dc = {}
        qdac._triggers = {"trigger_test": MagicMock()}  # exists, so we reach the cache check

        with pytest.raises(
            ValueError,
            match=f"No DC list with the given channel ID, first create a DC list with channel ID: {channel_id}",
        ):
            qdac.set_in_internal_trigger(channel_id, trigger)

    def test_start(self, qdac: QDevilQDac2, waveform: Square):
        channel_id = 4
        qdac.upload_awg_waveform(waveform, channel_id)
        qdac.upload_voltage_list(waveform, channel_id)
        trace = qdac._cache_awg[channel_id]
        dc_list = qdac._cache_dc[f"{qdac.device.name}_{channel_id}"]

        qdac.start()

        # the cached trace is wrapped in an AWG generator and started
        channel = qdac.device.channel.return_value
        channel.arbitrary_wave.assert_called_once_with(trace.name)
        channel.arbitrary_wave.return_value.start.assert_called_once()
        dc_list.start.assert_called_once()
        assert qdac._cache_awg == {}
        assert qdac._cache_dc == {}

    def test_clear_cache(self, qdac: QDevilQDac2):
        """Test clear_cache method"""
        qdac._cache_awg = {2: True}
        qdac.clear_cache()
        assert qdac._cache_awg == {}
        assert qdac._cache_dc == {}
        qdac.device.remove_traces.assert_called_once()

    def test_clear_trigger(self, qdac: QDevilQDac2, waveform: Square):
        """Test clear_trigger method"""
        qdac.clear_trigger()

        # Creating test trigger
        channel_id, trigger = 4, "trigger_test"
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.set_end_marker_internal_trigger(channel_id, trigger)

        qdac.clear_trigger(trigger)
        assert qdac._triggers == {}
        qdac.device.channel.return_value.write_channel.assert_any_call("SOUR{0}:DC:MARK:PEND 0")

    def test_clear_trigger_no_argument_clears_all_triggers(self, qdac: QDevilQDac2, waveform: Square):
        """clear_trigger() without a name frees every trigger of this instance (the platform cleanup path)."""
        qdac.upload_voltage_list(waveform, channel_id=4)
        qdac.upload_voltage_list(waveform, channel_id=2)
        qdac.set_start_marker_internal_trigger(channel_id=4, trigger="t1")
        qdac.set_end_marker_internal_trigger(channel_id=2, trigger="t2")
        assert len(qdac._triggers) == 2

        qdac.clear_trigger()

        assert qdac._triggers == {}
        qdac.device.channel.return_value.write_channel.assert_any_call("SOUR{0}:DC:MARK:PSTart 0")
        qdac.device.channel.return_value.write_channel.assert_any_call("SOUR{0}:DC:MARK:PEND 0")

    def test_internal_trigger_reusable_after_clear(self, qdac: QDevilQDac2, waveform: Square):
        """A freed internal trigger number is seen as free again on the next allocation."""
        qdac.upload_voltage_list(waveform, channel_id=4)
        qdac.set_start_marker_internal_trigger(channel_id=4, trigger="t1")
        assert qdac._triggers["t1"].value == 1

        qdac.clear_trigger("t1")
        qdac.set_start_marker_internal_trigger(channel_id=4, trigger="t1")

        # without rebuilding _internal_triggers from the instrument this would be 2
        assert qdac._triggers["t1"].value == 1

    def test_allocate_internal_trigger_limit_of_triggers_raises_error(self, qdac: QDevilQDac2):
        """When the instrument reports every internal trigger as busy, allocation fails."""
        channel = qdac.device.channel.return_value
        registers = list(product(qdac._GENERATOR_LIST, qdac._MARKER_LOCATION))[: qdac._N_INT_TRIGGERS]
        for trigger_number, (generator, location) in enumerate(registers, start=1):
            channel.write_channel(f"SOUR{{0}}:{generator}:MARK:{location} {trigger_number}")

        qdac_generator = MagicMock()
        with pytest.raises(ValueError, match="No free internal triggers"):
            qdac.allocate_internal_trigger(qdac_generator)
        assert len(qdac._internal_triggers) == qdac._N_INT_TRIGGERS

    def test_stop(self, qdac: QDevilQDac2, waveform: Square):
        channel_id = 4
        qdac._cache_dc = {}

        # Simulate running a dc pulse
        qdac.upload_voltage_list(waveform, channel_id)
        qdac.start()

        qdac.stop()
        qdac.device.channel(channel_id).dc_abort.assert_called()

    def test_input_range_runcard(self, qdac_out_range: QDevilQDac2):
        # Test that an error is raised when the input value on the runcard for the qdac are out of bound
        channel_id = 10
        error_string = re.escape(
            f"The ramp rate is out of range on channel {channel_id}. It should be between 0.01 V/s and 2e7 V/s."
        )
        with pytest.raises(ValueError, match=error_string):
            qdac_out_range.initial_setup()

    def test_input_range_set_parameter(self, qdac: QDevilQDac2):
        # Test that an error is raised when the input value on set_parameter RAMPING_RATE for the qdac are out of bound
        channel_id = 10
        error_string = re.escape(
            f"The ramp rate is out of range on channel {channel_id}. It should be between 0.01 V/s and 2e7 V/s."
        )
        with pytest.raises(ValueError, match=error_string):
            qdac.set_parameter(parameter=Parameter.RAMPING_RATE, value=0.0001, channel_id=channel_id)

    def test_input_range_set_parameter_enabled(self, qdac_out_range: QDevilQDac2):
        # Test that an error is raised when the input value on set_parameter RAMPING_ENABLED for the qdac are out of bound
        channel_id = 10
        error_string = re.escape(
            f"The ramp rate is out of range on channel {channel_id}. It should be between 0.01 V/s and 2e7 V/s."
        )
        with pytest.raises(ValueError, match=error_string):
            qdac_out_range.set_parameter(parameter=Parameter.RAMPING_ENABLED, value=True, channel_id=channel_id)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.VOLTAGE, -0.001),
            (Parameter.RAMPING_ENABLED, False),
            (Parameter.RAMPING_ENABLED, True),
            (Parameter.RAMPING_RATE, 0.05),
            (Parameter.SPAN, "high"),
            (Parameter.LOW_PASS_FILTER, "low"),
        ],
    )
    def test_set_parameter_method(self, qdac: QDevilQDac2, parameter: Parameter, value):
        """Test setup method"""
        for index, channel_id in enumerate(qdac.dacs):
            qdac.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

            channel_calls = []
            channel_calls.append(call(channel_id))
            if parameter == Parameter.VOLTAGE:
                channel_calls.append(call().dc_constant_V(value))
            if parameter == Parameter.SPAN:
                channel_calls.append(call().output_range(value))
            if parameter == Parameter.LOW_PASS_FILTER:
                channel_calls.append(call().output_filter(value))
            if parameter == Parameter.RAMPING_ENABLED:
                if value:
                    channel_calls.append(call().dc_slew_rate_V_per_s(qdac.ramp_rate[index]))
                else:
                    channel_calls.append(call().dc_slew_rate_V_per_s(2e7))
            if parameter == Parameter.RAMPING_RATE:
                if qdac.ramping_enabled[index]:
                    channel_calls.append(call().dc_slew_rate_V_per_s(qdac.ramp_rate[index]))

            qdac.device.channel.assert_has_calls(channel_calls)
            assert qdac.get_parameter(parameter=parameter, channel_id=channel_id) == value

    @pytest.mark.parametrize("parameter, value", [(Parameter.MAX_CURRENT, 0.001), (Parameter.GAIN, 0.0005)])
    def test_set_parameter_method_raises_exception(self, qdac: QDevilQDac2, parameter: Parameter, value):
        """Test the setup method raises an exception with wrong parameters"""
        for channel_id in qdac.dacs:
            with pytest.raises(ParameterNotFound):
                qdac.set_parameter(parameter, value, channel_id)

    @pytest.mark.parametrize("parameter, value", [(Parameter.MAX_CURRENT, 0.001), (Parameter.GAIN, 0.0005)])
    def test_get_parameter_method_raises_exception(self, qdac: QDevilQDac2, parameter: Parameter, value):
        """Test the get method raises an exception with wrong parameters"""
        for channel_id in qdac.dacs:
            with pytest.raises(ParameterNotFound):
                qdac.get_parameter(parameter, channel_id)

    @pytest.mark.parametrize("channel_id", [0, 25, -1, None])
    def test_validate_channel_method_raises_exception(self, qdac: QDevilQDac2, channel_id):
        """Test the _validate_channel method raises an exception with wrong parameters"""
        with pytest.raises(ValueError):
            qdac._validate_channel(channel_id)

    def test_qdac_to_qdac_consecutive_execution(self, qdac: QDevilQDac2, qdac_2: QDevilQDac2, waveform: Square):
        """qdac emits on out port 1; qdac_2 starts its DC list on in port 1."""
        qdac.device.name = "qdac"
        qdac_2.device.name = "qdac_2"

        qdac.upload_voltage_list(waveform, channel_id=4)
        qdac.set_out_external_trigger(channel_id=4, out_port=1, trigger="sync")
        qdac.device.connect_external_trigger.assert_called_once()

        qdac_2.upload_voltage_list(waveform, channel_id=3)
        qdac_2.set_in_external_trigger(channel_id=3, in_port=1)
        qdac_2._cache_dc["qdac_2_3"].start_on_external.assert_called_once_with(1)

    def test_two_users_shared_qdac_trigger_pool(self, qdac: QDevilQDac2, qdac_2: QDevilQDac2, waveform: Square):
        """Two connections to one physical QDAC: the second user sees the first
        user's allocated internal trigger and gets the next free one."""
        devices, channels = _shared_physical_qdac(2)
        qdac.device, qdac_2.device = devices

        # User 1: DC list + start marker on channel 4
        qdac.upload_voltage_list(waveform, channel_id=4)
        qdac.set_start_marker_internal_trigger(channel_id=4, trigger="t1")

        # User 2: same flow on channel 3 — scan finds trigger 1 busy, allocates 2
        qdac_2.upload_voltage_list(waveform, channel_id=3)
        qdac_2.set_start_marker_internal_trigger(channel_id=3, trigger="t1")

        assert qdac._triggers["t1"].value == 1
        assert qdac_2._triggers["t1"].value == 2

        # Each user's DC list is independent
        dc_list_1 = qdac._cache_dc["qdac_shared_4"]
        dc_list_2 = qdac_2._cache_dc["qdac_shared_3"]
        assert dc_list_1 is not dc_list_2

        # User 1 starts; user 2's list must not run
        qdac.start()
        dc_list_1.start.assert_called_once()
        dc_list_2.start.assert_not_called()
        assert qdac._cache_dc == {}
        assert set(qdac_2._cache_dc) == {"qdac_shared_3"}

        qdac_2.start()
        dc_list_2.start.assert_called_once()

        # User 1 frees their trigger: only channel 4's register is zeroed
        qdac.clear_trigger("t1")
        assert "t1" not in qdac._triggers
        assert "t1" in qdac_2._triggers
        ch3_writes = [c.args[0] for c in channels[3].write_channel.call_args_list]
        ch4_writes = [c.args[0] for c in channels[4].write_channel.call_args_list]
        assert any(w.upper().startswith("SOUR{0}:DC:MARK:PSTART 0") for w in ch4_writes)
        assert not any(w.endswith(" 0") for w in ch3_writes)
