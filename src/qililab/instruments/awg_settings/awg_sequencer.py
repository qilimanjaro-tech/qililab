""" AWG Sequencer """


from dataclasses import asdict, dataclass

from qililab.instruments.awg_settings.awg_sequencer_path import AWGSequencerPath
from qililab.instruments.awg_settings.typings import AWGSequencerPathIdentifier, AWGSequencerTypes
from qililab.utils.asdict_factory import dict_factory


@dataclass
class AWGSequencer:
    """AWG Sequencer

    Args:
        identifier (int): The identifier of the sequencer
        chip_port_id (int | None): Port identifier of the chip where a specific sequencer is connected to.
                                    By default, using the first sequencer
        path0 (AWGOutputChannel): AWG output channel associated with the path 0 sequencer
        path1 (AWGOutputChannel): AWG output channel associated with the path 1 sequencer
        intermediate_frequency (float): Frequency for each sequencer
        gain_imbalance (float): Amplitude added to the Q channel.
        phase_imbalance (float): Dephasing.
        hardware_modulation  (bool): Flag to determine if the modulation is performed by the device
        gain_path0 (float): Gain step used by the sequencer path0.
        gain_path1 (float): Gain step used by the sequencer path1.
        offset_path0 (float): Path0 or I offset (unitless). amplitude + offset should be in range [0 to 1].
        offset_path1 (float): Path1 or Q offset (unitless). amplitude + offset should be in range [0 to 1].
    """

    identifier: int
    chip_port_id: int | None
    path0: AWGSequencerPath | None
    path1: AWGSequencerPath | None
    intermediate_frequency: float
    gain_imbalance: float | None
    phase_imbalance: float | None
    hardware_modulation: bool
    gain_path0: float
    gain_path1: float
    offset_path0: float
    offset_path1: float

    def __post_init__(self):
        """Build path0 and path 1 AWGSequencerPaths"""
        if isinstance(self.path0, dict):
            self.path0 = AWGSequencerPath(
                path_id=AWGSequencerPathIdentifier.PATH0, **self.path0  # pylint: disable=not-a-mapping
            )
        if isinstance(self.path1, dict):
            self.path1 = AWGSequencerPath(
                path_id=AWGSequencerPathIdentifier.PATH1, **self.path1  # pylint: disable=not-a-mapping
            )

    @property
    def out_id_path0(self):
        """Return output channel identifier for path0"""
        if self.path0 is None:
            raise ValueError("path0 is not defined")
        return self.path0.output_channel.identifier

    @property
    def out_id_path1(self):
        """Return output channel identifier for path1"""
        if self.path1 is None:
            raise ValueError("path1 is not defined")
        return self.path1.output_channel.identifier

    def to_dict(self):
        """Return a dict representation of an AWG Sequencer."""
        result = asdict(self, dict_factory=dict_factory)
        if isinstance(self.path0, dict) and isinstance(self.path1, dict):
            return result
        result.pop(AWGSequencerTypes.PATH0.value)
        result.pop(AWGSequencerTypes.PATH1.value)
        return result | {
            AWGSequencerTypes.PATH0.value: self.path0.to_dict() if self.path0 is not None else None,
            AWGSequencerTypes.PATH1.value: self.path1.to_dict() if self.path1 is not None else None,
        }
