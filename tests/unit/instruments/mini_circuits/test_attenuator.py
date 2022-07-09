"""Tests for the Attenuator class."""
import urllib
from unittest.mock import MagicMock, patch

import pytest

from qililab.instruments import Attenuator


class TestAttenuator:
    """Unit tests checking the Attenuator attributes and methods."""

    def test_id_property(self, attenuator_no_device: Attenuator):
        """Test id property."""
        assert attenuator_no_device.id_ == attenuator_no_device.settings.id_

    def test_category_property(self, attenuator_no_device: Attenuator):
        """Test category property."""
        assert attenuator_no_device.category == attenuator_no_device.settings.category

    def test_attenuation_property(self, attenuator: Attenuator):
        """Test attenuation property."""
        assert hasattr(attenuator, "attenuation")
        assert attenuator.attenuation == attenuator.settings.attenuation

    @patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
    def test_setup_method(self, mock_urllib: MagicMock, attenuator: Attenuator):
        """Test setup method."""
        attenuator.setup()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()

    @patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
    def test_initial_setup_method(self, mock_urllib: MagicMock, attenuator: Attenuator):
        """Test initial setup method."""
        attenuator.initial_setup()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()

    def test_start_method(self, attenuator: Attenuator):
        """Test start method."""
        attenuator.start()

    def test_stop_method(self, attenuator: Attenuator):
        """Test stop method."""
        attenuator.stop()

    def test_reset_method(self, attenuator: Attenuator):
        """Test reset method."""
        attenuator.reset()

    @patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
    def test_http_request_raises_error(self, mock_urllib: MagicMock, attenuator: Attenuator):
        """Test delta property."""
        mock_urllib.error.URLError = urllib.error.URLError  # type: ignore
        mock_urllib.request.urlopen.side_effect = urllib.error.URLError(reason="")  # type: ignore
        with pytest.raises(ValueError):
            attenuator.setup()
        mock_urllib.request.urlopen.assert_called()
