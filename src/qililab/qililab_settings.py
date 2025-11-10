# Copyright 2025 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import tempfile
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class QililabSettings(BaseSettings):
    """
    Environment-based configuration settings for Qililab.

    These settings are automatically loaded from environment variables
    prefixed with `Qililab_`, or from a local `.env` file if present.
    """

    model_config = SettingsConfigDict(env_prefix="QILILAB_", env_file=".env", env_file_encoding="utf-8")

    experiment_results_base_path: str = Field(
        default=tempfile.gettempdir(),
        description="Base path for saving experiment results. [env: QILILAB_EXPERIMENT_RESULTS_BASE_PATH]",
    )
    experiment_results_path_format: str = Field(
        default="{date}/{time}/{label}.h5",
        description="Format of the experiment results path. [env: QILILAB_EXPERIMENT_RESULTS_PATH_FORMAT]",
    )
    experiment_results_save_in_database: bool = Field(
        default=False,
        description="If the experiment should be saved in the database or not. [env: QILILAB_EXPERIMENT_RESULTS_SAVE_IN_DATABASE]",
    )
    experiment_live_plot_enabled: bool = Field(
        default=False,
        description="If the experiment should be live plotted. [env: QILILAB_EXPERIMENT_LIVE_PLOT_ENABLED]",
    )
    experiment_live_plot_on_slurm: bool = Field(
        default=False,
        description="If the live plot is on slurm. [env: QILILAB_EXPERIMENT_LIVE_PLOT_ON_SLURM]",
    )
    experiment_live_plot_port: int | None = Field(
        default=None,
        description="The port number of the Dash server for when experiment_live_plot_on_slurm is True. Defaults to None. [env: QILILAB_EXPERIMENT_LIVE_PLOT_PORT]",
    )


@lru_cache(maxsize=1)
def get_settings() -> QililabSettings:
    """
    Returns a singleton instance of QililabSettings.

    This function caches the parsed environment-based settings to avoid
    redundant re-parsing across the application lifecycle.

    Returns:
        QililabSettings: The cached configuration object populated from environment variables.
    """
    return QililabSettings()
