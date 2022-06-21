"""Tests for the Attenuator class."""
import urllib
from unittest.mock import MagicMock, patch

import pytest

from qililab.instruments import Attenuator


class TestAttenuator:
    """Unit tests checking the Attenuator attributes and methods."""

    def test_id_property(self, attenuator: Attenuator):
        """Test id property."""
        assert attenuator.id_ == attenuator.settings.id_

    def test_category_property(self, attenuator: Attenuator):
        """Test category property."""
        assert attenuator.category == attenuator.settings.category

    def test_attenuation_property(self, attenuator: Attenuator):
        """Test attenuation property."""
        assert attenuator.attenuation == attenuator.settings.attenuation

    @patch("qililab.instruments.mini_circuits.attenuator.urllib", autospec=True)
    def test_setup_method(self, mock_urllib: MagicMock, attenuator: Attenuator):
        """Test setup method."""
        attenuator.connect()
        attenuator.setup()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()

    @patch("qililab.instruments.mini_circuits.attenuator.urllib", autospec=True)
    def test_http_request_raises_error(self, mock_urllib: MagicMock, attenuator: Attenuator):
        """Test delta property."""
        mock_urllib.error.URLError = urllib.error.URLError  # type: ignore
        mock_urllib.request.urlopen.side_effect = urllib.error.URLError(reason="")  # type: ignore
        with pytest.raises(ValueError):
            attenuator.connect()
        mock_urllib.request.urlopen.assert_called()
