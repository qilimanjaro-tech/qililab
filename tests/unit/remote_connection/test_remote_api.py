""" Tests for the Remote API """


from unittest.mock import MagicMock, patch

import pytest
from qiboconnection.api import API
from requests import HTTPError

from qililab.remote_connection.remote_api import RemoteAPI


class TestRemoteAPI:
    """Unit tests checking the Experiment attributes and methods"""

    def test_remote_api_instance_with_connection_none(self):
        """Test remote api instance with no connection."""
        remote_api = RemoteAPI()
        assert isinstance(remote_api, RemoteAPI)
        assert remote_api._blocked_device is False  # pylint: disable=protected-access

    def test_remote_api_does_not_activate_context_with_connection_none(self):
        """test remote api does not activate context with connection none."""
        remote_api = RemoteAPI()
        with remote_api:
            assert remote_api._blocked_device is False  # pylint: disable=protected-access
        assert remote_api._blocked_device is False  # pylint: disable=protected-access

    def test_remote_api_instance_with_active_connection(self, mocked_api: API):
        """Test remote api instance with no connection."""
        remote_api = RemoteAPI(connection=mocked_api)
        assert isinstance(remote_api, RemoteAPI)
        assert remote_api.connection is not None
        assert isinstance(remote_api.connection, API)

    @patch("qiboconnection.api.API.block_device_id", autospec=True)
    @patch("qiboconnection.api.API.release_device", autospec=True)
    def test_connection_is_blocked_when_enter_and_released_when_exit(
        self, mock_release_device: MagicMock, mock_block_device: MagicMock, mocked_remote_api: RemoteAPI
    ):
        """test connection is blocked when enter and relesed when exit"""
        with mocked_remote_api:
            assert mocked_remote_api._blocked_device is True  # pylint: disable=protected-access
            mock_block_device.assert_called_once()
        assert mocked_remote_api._blocked_device is False  # pylint: disable=protected-access
        mock_release_device.assert_called_once()

    @patch(
        "qiboconnection.api.API.block_device_id",
        autospec=True,
        side_effect=HTTPError("Device Galadriel Qblox rack is already busy"),
    )
    @patch("qiboconnection.api.API.release_device", autospec=True)
    def test_connection_does_not_release_device_when_is_already_blocked(
        self, mock_release_device: MagicMock, mock_block_device: MagicMock, mocked_remote_api: RemoteAPI
    ):
        """test connection does not release device when is already blocked"""
        with pytest.raises(HTTPError):
            with mocked_remote_api:
                mock_block_device.assert_called_once()
                assert mocked_remote_api._blocked_device is False  # pylint: disable=protected-access
            assert mocked_remote_api._blocked_device is False  # pylint: disable=protected-access
            mock_release_device.assert_not_called()
