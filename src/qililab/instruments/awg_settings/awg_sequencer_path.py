""" AWG Sequencer Path """


from dataclasses import dataclass


@dataclass
class AWGSequencerPath:
    """AWG Channel Mapping"""

    path_id: int
    output_channel: int

    def to_dict(self):
        """Return a dict representation of an AWG Sequencer Path."""
        return {"output_channel": self.output_channel}
