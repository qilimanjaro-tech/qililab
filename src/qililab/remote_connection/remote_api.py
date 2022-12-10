""" Remote API class """
from dataclasses import dataclass, field

from qiboconnection.api import API

from qililab.constants import GALADRIEL_DEVICE_ID


@dataclass
class RemoteAPI:
    """Remote API class"""

    connection: API | None = field(default=None)
    device_id: int | None = field(default=GALADRIEL_DEVICE_ID)
    manual_override: bool = field(default=False)
    _blocked_device: bool = field(init=False)

    def __post_init__(self):
        """Post initial initialization"""
        self._blocked_device = False
        if self.device_id is None:
            self.device_id = GALADRIEL_DEVICE_ID

    def block_remote_device(self):
        """Block the remote API device
        If:
            1. there is a connection and,
            2. this control has not been overriden,
        Then it blocks the device.
        """
        if (self.connection is not None) and (not self.manual_override) and not self._blocked_device:
            self.connection.block_device_id(device_id=self.device_id)
            self._blocked_device = True

    def release_remote_device(self) -> None:
        """Release the remote API device when:
            1. there is a connection,
            2. the device is blocked and,
            3. this control has not been overriden,
        Then it unblocks the device.
        """
        if (self.connection is not None and self._blocked_device) and (not self.manual_override):
            self.connection.release_device(device_id=self.device_id)
            self._blocked_device = False
