"""Platform class."""
from qililab.typings.yaml_type import yaml
from qililab.buses.interfaces.bus import BusInterface
from qililab.config import logger
from qililab.constants import RUNCARD
from qililab.instruments.instrument import Instrument
from qililab.instruments.instruments import Instruments
from qililab.instruments.utils import InstrumentFactory

class Platform:
    """Platform object that describes setup used to control quantum devices.

    Args:
        runcard_name (str): runcard name.
    """

    def __init__(self, runcard_name: str):
        self.settings = self._load_runcard(runcard_name)
        instruments = self.settings['instruments']
        buses = self.settings['buses']

        self.instruments = (
            Instruments(elements=self._load_instruments(instruments_dict=instruments))
            if instruments is not None
            else None
        )

        self.buses = self._load_buses(buses)

    def _load_runcard(self, runcard_name:str):
        """Loads a runcard"""
        with open(runcard_name, "r", encoding='utf-8') as stream:
            try:
                runcard = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        return runcard

    def _load_instruments(self, instruments_dict: list[dict]) -> list[Instrument]:
        """Instantiate all instrument classes from their respective dictionaries.

        Args:
            instruments_dict (list[dict]): List of dictionaries containing the settings of each instrument.

        Returns:
            list[Instrument]: List of instantiated instrument classes.
        """
        return [
            InstrumentFactory.get(instrument.pop(RUNCARD.TYPE))(settings=instrument) for instrument in instruments_dict
        ]

    def _load_buses(self, buses: list[dict]) -> list[BusInterface]:
        """Instantiate all buses classes from their respective dictionaries.

        Args:
            buses_dict (list[dict]): List of dictionaries containing the settings of each bus.

        Returns:
            list[BusInterface]: List of instantiated buses classes.
        """
        # only supporting DriveBus class for this research task
        for bus in buses:
            if bus['type'] == 'DriveBus':
                awg_settings = bus['AWG']
                
                
        return []

    def find_instrument(self, instruments_dict: dict, key: str, value: str) -> dict:
        """Finds an instrument settings by key and value from a dictionary of instruments recursively.

        Args:
            instruments_dict (list[dict]): List of dictionaries containing the settings of each instrument.

        Returns:
            dict: dictionary with the instrument settings.
        """
        for instrument in instruments_dict:
            if key in instrument and value in instrument[key]:
                return instrument
            elif 'submodules' in instrument:
                for submodule in instrument['submodules']:
                    if key in submodule and value in submodule[key]:
                        return instrument
        return {}

    def initial_setup(self):
        """Set the initial setup of the instruments"""
        # self.instrument_controllers.initial_setup()
        logger.info("Initial setup applied to the instruments")
