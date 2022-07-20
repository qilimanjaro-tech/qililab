""" Tests for the Remote API """

import pytest
from requests import HTTPError

from qililab.remote_connection.remote_api import RemoteAPI


class TestRemoteAPI:
    """Integration test checking the Experiment attributes and methods"""

    def test_connection_is_blocked_when_enter_and_released_when_exit(self, valid_remote_api: RemoteAPI):
        """test connection is blocked when enter and relesed when exit"""
        with valid_remote_api:
            assert valid_remote_api._blocked_device is True  # pylint: disable=protected-access
        assert valid_remote_api._blocked_device is False  # pylint: disable=protected-access

    def test_connection_raises_error_when_connection_is_already_blocked(
        self, valid_remote_api: RemoteAPI, second_valid_remote_api: RemoteAPI
    ):
        """test connection raises error when connection is already blocked"""
        with pytest.raises(HTTPError):
            with valid_remote_api:
                assert valid_remote_api._blocked_device is True  # pylint: disable=protected-access
                with second_valid_remote_api:
                    assert second_valid_remote_api._blocked_device is False  # pylint: disable=protected-access
            assert valid_remote_api._blocked_device is False  # pylint: disable=protected-access
