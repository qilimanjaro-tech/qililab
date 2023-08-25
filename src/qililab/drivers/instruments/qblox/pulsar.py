"""Driver for the Qblox Pulsar class."""
from typing import Any

from qblox_instruments.qcodes_drivers import Pulsar as QcodesPulsar
from qcodes.instrument.channel import ChannelTuple, InstrumentModule

from qililab.drivers.instruments.instrument_factory import InstrumentDriverFactory
from qililab.drivers.interfaces.base_instrument import BaseInstrument

from .sequencer_qcm import SequencerQCM
from .sequencer_qrm import SequencerQRM


@InstrumentDriverFactory.register
class Pulsar(QcodesPulsar, BaseInstrument):  # pylint: disable=abstract-method
    """Qililab's driver for QBlox-instruments Pulsar"""

    def __init__(self, alias: str, address: str | None = None, sequencers: list[str] | None = None, **kwargs):
        """Initialise the instrument.

        Args:
            alias (str): Pulsar name
            address (str): Instrument address
        """
        port = kwargs.get("port", None)
        debug = kwargs.get("debug", None)
        dummy_type = kwargs.get("dummy_type", None)
        super().__init__(name=alias, identifier=address, port=port, debug=debug, dummy_type=dummy_type)

        # Add sequencers
        self.submodules: dict[str, SequencerQCM | SequencerQRM] = {}  # resetting superclass submodules
        self.instrument_modules: dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self._channel_lists: dict[str, ChannelTuple] = {}  # resetting superclass channel lists

        sequencer_class = SequencerQCM if self.is_qcm_type else SequencerQRM
        if sequencers is not None:
            for seq_idx, seq_name in enumerate(sequencers):
                seq = sequencer_class(parent=self, name=seq_name, seq_idx=seq_idx)  # type: ignore
                self.add_submodule(seq_name, seq)
        else:
            for seq_idx in range(6):
                seq = sequencer_class(parent=self, name=f"sequencer{seq_idx}", seq_idx=seq_idx)  # type: ignore
                self.add_submodule(f"sequencer{seq_idx}", seq)

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name

    def instrument_repr(self) -> dict[str, Any]:
        """Returns a dictionary representation of the instrument, parameters and submodules.

        Returns:
            inst_repr (dict[str, Any]): Instrument representation
        """
        inst_repr: dict[str, Any] = {"alias": self.alias}
        if self.identifier:
            inst_repr["address"] = self.identifier
        if self.port:
            inst_repr["port"] = self.port
        if self.dummy_type:
            inst_repr["dummy_type"] = self.dummy_type

        params: dict[str, Any] = {}
        for param_name in self.params:
            param_value = self.get(param_name)
            params[param_name] = param_value
        inst_repr["parameters"] = params

        sequencers = [submodule for submodule in self.submodules]
        inst_repr["sequencers"] = sequencers

        return inst_repr
