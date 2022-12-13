""" AWG IQ Channel """


from dataclasses import dataclass

from qililab.instruments.awg_settings.awg_channel_mapping import AWGChannelMapping


@dataclass
class AWGIQChannel:
    """AWG IQ Channel

    Args:
        identifier (int): The identifier of the sequencer
        i_channel (AWGOutputChannel): AWG Ouput channel associated with the I Channel
        q_channel (AWGOutputChannel): AWG Ouput channel associated with the Q Channel
    """

    identifier: int
    i_channel: AWGChannelMapping
    q_channel: AWGChannelMapping

    def __post_init__(self):
        """Build I and Q channels"""
        if isinstance(self.i_channel, dict):
            self.i_channel = AWGChannelMapping(**self.i_channel)  # pylint: disable=not-a-mapping
        if isinstance(self.q_channel, dict):
            self.q_channel = AWGChannelMapping(**self.q_channel)  # pylint: disable=not-a-mapping

    @property
    def sequencer_id_i_channel(self):
        """Return the sequencer identifier for the I Channel"""
        return self.i_channel.awg_sequencer_identifier

    @property
    def sequencer_path_i_channel(self) -> int:
        """Return the sequencer path identifier for the I Channel"""
        return self.i_channel.awg_sequencer_path_identifier.value

    @property
    def sequencer_id_q_channel(self):
        """Return the sequencer identifier for the Q Channel"""
        return self.q_channel.awg_sequencer_identifier

    @property
    def sequencer_path_q_channel(self) -> int:
        """Return the sequencer path identifier for the Q Channel"""
        return self.q_channel.awg_sequencer_path_identifier.value
