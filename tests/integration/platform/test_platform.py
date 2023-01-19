"""Tests for the Platform class."""
import datetime
import os
from unittest.mock import MagicMock, patch

import pytest
from qiboconnection.runcard import Runcard as QiboconnectionRuncard

from qililab import __version__, save_platform
from qililab.constants import DEFAULT_PLATFORM_NAME, RUNCARDS
from qililab.platform import Platform, build_platform
from qililab.remote_connection import RemoteAPI
from qililab.settings import RuncardSchema

from ...conftest import platform_db, platform_yaml
from ...data import Galadriel


def _clean_local_files(platform: Platform):
    """Remove local yaml files created at platform dump"""
    os.remove(f"{os.environ.get(RUNCARDS, None)}/{platform.name}.yml")


class TestPlatform:
    """Integration tests checking the Platform attributes and methods."""

    def test_platform_manager_local_cycle(self):
        """Test PlatformManager dump method."""

        platform = Platform(RuncardSchema(**Galadriel.runcard))
        platform.settings.name = f"test_{platform.name}"

        save_platform(platform=platform, database=False)
        written_read_platform = build_platform(name=platform.name, database=False)

        assert isinstance(written_read_platform, Platform)
        assert (
            platform.to_dict() == written_read_platform.to_dict()
        ), "Initial and local written-read platforms should contain the same information "

        _clean_local_files(platform=platform)

    @patch("qililab.remote_connection.remote_api.RemoteAPI.connection")
    def test_platform_manager_remote_cycle(self, mocked_remote_connection: MagicMock):
        """Test build method loading from YAML."""

        platform = Platform(RuncardSchema(**Galadriel.runcard))
        mocked_remote_connection.save_runcard.return_value = 0
        mocked_remote_connection.get_runcard.return_value = QiboconnectionRuncard(
            name=DEFAULT_PLATFORM_NAME,
            id=0,
            user_id=0,
            device_id=0,
            description="",
            runcard=platform.to_dict(),
            qililab_version=__version__,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

        mocked_remote_connection.save_runcard.return_value = 0
        remote_api = RemoteAPI(connection=mocked_remote_connection, device_id=0)

        save_platform(platform=platform, database=True, remote_api=remote_api, description="TEST")
        written_read_platform = build_platform(name=DEFAULT_PLATFORM_NAME, database=True, remote_api=remote_api)

        assert isinstance(written_read_platform, Platform)
        assert (
            written_read_platform.to_dict() == platform.to_dict()
        ), "Initial and remote written-read platforms should contain the same information "
