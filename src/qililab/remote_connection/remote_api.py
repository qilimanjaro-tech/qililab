""" Remote API class """
from dataclasses import dataclass, field

from qiboconnection.api import API

from qililab.constants import GALADRIEL_DEVICE_ID


@dataclass
class RemoteAPI:
    """Remote API class"""

    connection: API | None = field(default=None)
    device_id: int | None = field(default=GALADRIEL_DEVICE_ID)
    _blocked_device: bool = field(init=False)
    manual_override: bool = field(init=False)

    def __post_init__(self):
        """Post initial initialization"""
        self._blocked_device = False
        if self.device_id is None:
            self.device_id = GALADRIEL_DEVICE_ID

    def __enter__(self):
        """Code executed when starting a with statement."""
        if (self.connection is not None) and (not self.manual_override):
            self.connection.block_device_id(device_id=self.device_id)
            self._blocked_device = True

    def __exit__(self, exc_type, exc_value, traceback):
        """Code executed when stopping a with statement."""
        if (self.connection is not None and self._blocked_device) and (not self.manual_override):
            self.connection.release_device(device_id=self.device_id)
            self._blocked_device = False
