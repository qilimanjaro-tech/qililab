"""Unit tests for the AWGSequencer class."""
import copy

import pytest

from qililab.instruments.awg_settings import AWGSequencer


def awg_settings(output_i: int = 0, output_q: int = 1):
    return {
        "identifier": 0,
        "chip_port_id": 1,
        "output_i": output_i,
        "output_q": output_q,
        "intermediate_frequency": 20000000,
        "gain_i": 0.001,
        "gain_q": 0.02,
        "gain_imbalance": 1,
        "phase_imbalance": 0,
        "offset_i": 0,
        "offset_q": 0,
        "hardware_modulation": True,
    }


class TestInitialization:
    """Unit tests for the initialization of the AWGSequencer class."""

    def test_init(self):
        """Test the __init__ method of the AWGSequencer class."""
        settings = awg_settings()
        awg_sequencer = AWGSequencer(**settings)
        assert awg_sequencer.identifier == settings["identifier"]
        assert awg_sequencer.chip_port_id == settings["chip_port_id"]
        assert awg_sequencer.output_i == settings["output_i"]
        assert awg_sequencer.output_q == settings["output_q"]
        assert awg_sequencer.intermediate_frequency == settings["intermediate_frequency"]
        assert awg_sequencer.gain_i == settings["gain_i"]
        assert awg_sequencer.gain_q == settings["gain_q"]
        assert awg_sequencer.gain_imbalance == settings["gain_imbalance"]
        assert awg_sequencer.phase_imbalance == settings["phase_imbalance"]
        assert awg_sequencer.offset_i == settings["offset_i"]
        assert awg_sequencer.offset_q == settings["offset_q"]
        assert awg_sequencer.hardware_modulation == settings["hardware_modulation"]
        assert awg_sequencer.path_i == 0
        assert awg_sequencer.path_q == 1

    @pytest.mark.parametrize("output_i, output_q", ((1, 0), (1, 2), (3, 0), (3, 2)))
    def test_init_swapped_paths(self, output_i, output_q):
        """Test the __init__ method when the I channel is mapped to an odd output and the Q channel to an even
        output."""
        settings = awg_settings(output_i=output_i, output_q=output_q)
        awg_sequencer = AWGSequencer(**settings)
        assert awg_sequencer.path_i == 1
        assert awg_sequencer.path_q == 0

    @pytest.mark.parametrize("output_i, output_q", ((0, 0), (1, 1), (0, 2), (1, 3)))
    def test_both_channels_have_odd_or_even_outputs_raises_error(self, output_i, output_q):
        """Test that if both I/Q channels are mapped to an odd/even output an error is raised."""
        settings = awg_settings(output_i=output_i, output_q=output_q)
        with pytest.raises(
            ValueError, match=f"Cannot map both paths of sequencer {settings['identifier']} into an even/odd output."
        ):
            AWGSequencer(**settings)


class TestMethods:
    """Unit tests for the methods of the AWGSequencer class."""

    def test_to_dict(self):
        """Test the `to_dict` method of the AWGSequencer class."""
        settings = awg_settings()
        awg_sequencer = AWGSequencer(**settings)
        assert awg_sequencer.to_dict() == settings
