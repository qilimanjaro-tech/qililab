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

    def test_remote_api_instance_with_mocked_api(self, mocked_api: API):
        """Test remote api instance with mocked api."""
        remote_api = RemoteAPI(connection=mocked_api)
        assert isinstance(remote_api, RemoteAPI)
        assert remote_api.connection is not None
        assert isinstance(remote_api.connection, API)

    @patch("qiboconnection.api.API.block_device_id", autospec=True)
    @patch("qiboconnection.api.API.release_device", autospec=True)
    def test_connection_is_blocked_when_block_and_release_method_device(
        self, mock_release_device: MagicMock, mock_block_device: MagicMock, mocked_remote_api: RemoteAPI
    ):
        """test connection is blocked when enter and relesed when exit"""
        mocked_remote_api.block_remote_device()
        assert mocked_remote_api._blocked_device is True  # pylint: disable=protected-access
        mock_block_device.assert_called_once()
        mocked_remote_api.release_remote_device()
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
            mocked_remote_api.block_remote_device()
            mock_block_device.assert_called_once()
            assert mocked_remote_api._blocked_device is False  # pylint: disable=protected-access
            mock_release_device.assert_not_called()

    @patch("qiboconnection.api.API.block_device_id", autospec=True)
    @patch("qiboconnection.api.API.release_device", autospec=True)
    def test_override_avoids_calls_to_block_unblock(
        self, mock_release_device: MagicMock, mock_block_device: MagicMock, mocked_remote_api: RemoteAPI
    ):
        """test connection is blocked when enter and relesed when exit"""
        previous_status_block = mocked_remote_api._blocked_device  # pylint: disable=protected-access
        mocked_remote_api.manual_override = True
        mocked_remote_api.block_remote_device()
        assert mocked_remote_api._blocked_device is previous_status_block  # pylint: disable=protected-access
        mock_block_device.assert_not_called()
        mock_release_device.assert_not_called()
