from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from qililab import PLATFORM_MANAGER_YAML
from qililab.platform import PlatformManagerYAML

from .utils.side_effect import yaml_safe_load_side_effect


@pytest.fixture(name="platform_builder_yaml")
@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_platform_builder_yaml(mock_load: MagicMock):
    """Return PlatformBuilderYAML instance with loaded platform."""
    filepath = Path(__file__).parent.parent.parent / "examples" / "all_platform.yml"
    PLATFORM_MANAGER_YAML.build_from_yaml(filepath=str(filepath))
    mock_load.assert_called()
    return PLATFORM_MANAGER_YAML


class TestPlatformBuilderDB:
    """Unit tests checking the PlatformBuilderDB attributes and methods."""

    def test_build_raises_attribute_error(self):
        """Test build method raises attribute error."""
        platform_builder = PlatformManagerYAML()
        with pytest.raises(AttributeError):
            platform_builder.build(platform_name="platform_0")
