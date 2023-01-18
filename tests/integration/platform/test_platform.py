"""Tests for the Platform class."""
import datetime
from unittest.mock import MagicMock, patch

import pytest
from qiboconnection.runcard import Runcard as QiboconnectionRuncard

from qililab import __version__, save_platform
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.platform import Platform, build_platform
from qililab.remote_connection import RemoteAPI

from ...conftest import platform_db, platform_yaml


@pytest.mark.parametrize("platform", [platform_db(), platform_yaml()])
class TestPlatform:
    """Integration tests checking the Platform attributes and methods."""

    @patch("qililab.remote_connection.remote_api.RemoteAPI.connection")
    @patch("yaml.dump")
    def test_platform_manager_dump_method(
        self, yaml_dump: MagicMock, mocked_remote_connection: MagicMock, platform: Platform
    ):
        """Test PlatformManager dump method."""

        save_platform(platform=platform)
        yaml_dump.assert_called()

        mocked_remote_connection.save_runcard.return_value = 0
        remote_api = RemoteAPI(connection=mocked_remote_connection, device_id=0)
        save_platform(platform=platform, database=True, remote_api=remote_api, description="TEST")
        remote_api.connection.save_runcard.assert_called()  # type: ignore

    @patch("qililab.remote_connection.remote_api.RemoteAPI.connection")
    @patch("yaml.safe_load")
    def test_build_platform_method(self, yaml_load: MagicMock, mocked_remote_connection: MagicMock, platform: Platform):
        """Test build method loading from YAML."""

        yaml_load.return_value = platform.to_dict()
        local_platform = build_platform(name=DEFAULT_PLATFORM_NAME, database=False)
        assert isinstance(local_platform, Platform)

        mocked_remote_connection.get_runcard.return_value = QiboconnectionRuncard(
            name=DEFAULT_PLATFORM_NAME,
            id=0,
            user_id=0,
            device_id=0,
            description="",
            runcard=local_platform.to_dict(),
            qililab_version=__version__,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        remote_api = RemoteAPI(connection=mocked_remote_connection, device_id=0)
        remote_platform = build_platform(name=DEFAULT_PLATFORM_NAME, database=True, remote_api=remote_api)
        assert isinstance(remote_platform, Platform)

        assert local_platform.to_dict() == remote_platform.to_dict(), (
            "Local and remote platforms should be built " "equivalently "
        )
