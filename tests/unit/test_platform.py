from unittest.mock import MagicMock, patch

import pytest

from qililab import PLATFORM_BUILDER_DB
from qililab.platforms import Platform, PlatformBuilderDB

from .utils.side_effect import yaml_safe_load_side_effect


@pytest.fixture(name="platform_builder_db")
@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_platform_builder_db(mock_load: MagicMock):
    """Return PlatformBuilderDB instance with loaded platform."""
    PLATFORM_BUILDER_DB.build(platform_name="platform_0")
    mock_load.assert_called()
    return PLATFORM_BUILDER_DB


class TestPlatform:
    """Unit tests checking the Platform attributes and methods."""

    def test_platform_attribute(self, platform_builder_db: PlatformBuilderDB):
        """Test platform attribute."""
        assert isinstance(platform_builder_db.platform, Platform)
