"""Unit tests for the AWGSequencer class."""
from qililab.instruments.awg_settings import AWGSequencer


def awg_settings():
    return {
        "identifier": 0,
        "outputs": [0, 1],
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
        assert awg_sequencer.outputs == settings["outputs"]
        assert awg_sequencer.intermediate_frequency == settings["intermediate_frequency"]
        assert awg_sequencer.gain_i == settings["gain_i"]
        assert awg_sequencer.gain_q == settings["gain_q"]
        assert awg_sequencer.gain_imbalance == settings["gain_imbalance"]
        assert awg_sequencer.phase_imbalance == settings["phase_imbalance"]
        assert awg_sequencer.offset_i == settings["offset_i"]
        assert awg_sequencer.offset_q == settings["offset_q"]
        assert awg_sequencer.hardware_modulation == settings["hardware_modulation"]


class TestMethods:
    """Unit tests for the methods of the AWGSequencer class."""

    def test_to_dict(self):
        """Test the `to_dict` method of the AWGSequencer class."""
        settings = awg_settings()
        awg_sequencer = AWGSequencer(**settings)
        assert awg_sequencer.to_dict() == settings
