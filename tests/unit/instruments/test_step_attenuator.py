"""Tests for the StepAttenuator class."""
import urllib
from unittest.mock import MagicMock, patch

import pytest

from qililab.instruments import StepAttenuator


class TestStepAttenuator:
    """Unit tests checking the StepAttenuator attributes and methods."""

    def test_id_property(self, step_attenuator: StepAttenuator):
        """Test id property."""
        assert step_attenuator.id_ == step_attenuator.settings.id_

    def test_category_property(self, step_attenuator: StepAttenuator):
        """Test category property."""
        assert step_attenuator.category == step_attenuator.settings.category

    def test_attenuation_property(self, step_attenuator: StepAttenuator):
        """Test attenuation property."""
        assert step_attenuator.attenuation == step_attenuator.settings.attenuation

    @patch("qililab.instruments.mini_circuits.step_attenuator.urllib", autospec=True)
    def test_setup_method(self, mock_urllib: MagicMock, step_attenuator: StepAttenuator):
        """Test setup method."""
        step_attenuator.connect()
        step_attenuator.setup()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()

    @patch("qililab.instruments.mini_circuits.step_attenuator.urllib", autospec=True)
    def test_http_request_raises_error(self, mock_urllib: MagicMock, step_attenuator: StepAttenuator):
        """Test delta property."""
        mock_urllib.error.URLError = urllib.error.URLError  # type: ignore
        mock_urllib.request.urlopen.side_effect = urllib.error.URLError(reason="")  # type: ignore
        with pytest.raises(ValueError):
            step_attenuator.connect()
        mock_urllib.request.urlopen.assert_called()
