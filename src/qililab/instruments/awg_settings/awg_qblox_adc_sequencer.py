""" AWG Qblox ADC Sequencer """


from dataclasses import dataclass, field

from qililab.instruments.awg_settings.awg_adc_sequencer import AWGADCSequencer
from qililab.instruments.awg_settings.awg_qblox_sequencer import AWGQbloxSequencer


@dataclass
class AWGQbloxADCSequencer(AWGQbloxSequencer, AWGADCSequencer):
    """AWG Qblox ADC Sequencer"""

    weights_path0: list[float]
    weights_path1: list[float]
    weighed_acq_enabled: bool
    threshold: float
    used_integration_length: int = field(init=False)

    def __post_init__(self):
        super().__post_init__()
        self._verify_weights()
        self._determine_used_integration_length()

    def _verify_weights(self):
        """Verifies that the length of weights_path0 and weights_path1 are equal.

        Raises:
            IndexError: The length of weights_path0 and weights_path1 must be equal.
        """
        if len(self.weights_path0) != len(self.weights_path1):
            raise IndexError("The length of weights_path0 and weights_path1 must be equal.")

    def _determine_used_integration_length(self):
        """Determines the used integration length. Length of the weights if using weighed acquisition, integration_length otherwise."""
        self.used_integration_length = len(self.weights_path0) if self.weighed_acq_enabled else self.integration_length
