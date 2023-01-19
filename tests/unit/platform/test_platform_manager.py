"""Tests for PlatformManagerYAML class."""
import datetime
from unittest.mock import MagicMock, patch

from qiboconnection.runcard import Runcard as QiboconnectionRuncard

from qililab import __version__, build_platform, save_platform
from qililab.platform import Platform
from qililab.remote_connection import RemoteAPI
from qililab.settings import RuncardSchema

from ...data import Galadriel


class TestPlatformManager:
    """Unit tests checking the Platform attributes and methods."""

    @patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard)
    @patch("qililab.platform.platform_manager_yaml.open")
    def test_build_local_method(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test build method from YAML file."""

        platform = build_platform(name="galadriel", database=False)

        assert isinstance(platform, Platform)
        mock_load.assert_called_once()
        mock_open.assert_called_once()

    @patch("qililab.platform.platform_manager_yaml.yaml.dump")
    def test_dump_local_method(self, mock_dump: MagicMock):
        """Test dump method from YAML file."""
        platform = Platform(RuncardSchema(**Galadriel.runcard))

        save_platform(platform=platform, database=False)

        mock_dump.assert_called_once()

    @patch("qililab.remote_connection.remote_api.RemoteAPI.connection")
    def test_build_remote_method(self, mock_connection: MagicMock):
        """Test build method from DB."""

        mock_connection.get_runcard.return_value = QiboconnectionRuncard(
            name="galadriel",
            id=0,
            user_id=0,
            device_id=0,
            description="",
            runcard=Galadriel.runcard,
            qililab_version=__version__,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        remote_api = RemoteAPI(connection=mock_connection, device_id=0)

        platform = build_platform(name="galadriel", database=True, remote_api=remote_api)

        assert isinstance(platform, Platform)
        mock_connection.get_runcard.assert_called()

    @patch("qililab.remote_connection.remote_api.RemoteAPI.connection")
    def test_dump_remote_method(self, mocked_remote_connection: MagicMock):
        """Test dump method to DB."""
        platform = Platform(RuncardSchema(**Galadriel.runcard))
        mocked_remote_connection.save_runcard.return_value = 0
        remote_api = RemoteAPI(connection=mocked_remote_connection, device_id=0)

        save_platform(platform=platform, database=True, remote_api=remote_api, description="TEST")

        remote_api.connection.save_runcard.assert_called()
