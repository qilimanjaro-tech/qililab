from qblox_instruments.qcodes_drivers import Pulsar
from qblox_instruments.qcodes_drivers.sequencer import Sequencer
from qililab._drivers import Digitiser
from qililab.config import logger
from qililab.result.qblox_results.qblox_result import QbloxResult


class AWGSequencer(Sequencer, AWG):
    def execute(self, program):
        ...


class AWGDigitiserSequencer(Sequencer, AWG, Digitiser):
    def execute(self, program):
        ...

    def get_results(self) -> QbloxResult:
       """Wait for sequencer to finish sequence, wait for acquisition to finish and get the acquisition results.
        If any of the timeouts is reached, a TimeoutError is raised.

        Returns:
            QbloxResult: Class containing the acquisition results.

        """
        flags = self.get_sequencer_state
        logger.info("Sequencer[%d] flags: \n%s", self.idx, flags)
        self.get_acquisition_state
        if self.store_scope_acquisition:
            self.parent.store_scope_acquisition(sequencer=self.idx, name="default")
        results = [self._get_acq_acquisition_data["default"]["acquisition"]]
        self.sync_en(False)
        integration_lengths = [self.integration_length_acq]

        # flags = self.device.get_sequencer_state(
        #             sequencer=sequencer_id, timeout=cast(AWGQbloxADCSequencer, sequencer).sequence_timeout
        #         )
        #         logger.info("Sequencer[%d] flags: \n%s", sequencer_id, flags)
        #         self.device.get_acquisition_state(
        #             sequencer=sequencer_id, timeout=cast(AWGQbloxADCSequencer, sequencer).acquisition_timeout
        #         )
# 
        #         if sequencer.scope_store_enabled:
        #             self.device.store_scope_acquisition(sequencer=sequencer_id, name="default")
# 
        #         results.append(self.device.get_acquisitions(sequencer=sequencer.identifier)["default"]["acquisition"])
        #         self.device.sequencers[sequencer.identifier].sync_en(False)
# 
        return QbloxResult(integration_lengths=integration_lengths, qblox_raw_results=results)


class QililabPulsar(Pulsar):
    def __init__(self, name: str, address: str | None = None, **kwargs):
        super().__init__(name, address, **kwargs)

        # Add sequencers
        for seq_idx in range(6):
            if self.is_qrm_type:
                seq = AWGDigitiserSequencer(self, f"sequencer{seq_idx}", seq_idx)
            else:
                seq = AWGSequencer(self, f"sequencer{seq_idx}", seq_idx)

            self.add_submodule(f"sequencer{seq_idx}", seq)