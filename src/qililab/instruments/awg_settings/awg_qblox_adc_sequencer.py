""" AWG Qblox ADC Sequencer """


from dataclasses import dataclass

from qililab.instruments.awg_settings.awg_adc_sequencer import AWGADCSequencer
from qililab.instruments.awg_settings.awg_qblox_sequencer import AWGQbloxSequencer


@dataclass
class AWGQbloxADCSequencer(AWGQbloxSequencer, AWGADCSequencer):
    """AWG Qblox ADC Sequencer"""

    weights_path0: list[float]
    weights_path1: list[float]
    weighed_acq_enabled: bool
