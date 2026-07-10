"""Load versioned YAML configs from config/ directory.

Every config carries its own *_config_id (see config/README.md conventions).
Loaders validate that the id field exists so nothing anonymous reaches runtime.
"""

from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"

_ID_FIELDS = {
    "retrieval.yaml": "retrieval_config_id",
    "prompts.yaml": "prompt_id",
    "model_gateway.yaml": "gateway_config_id",
    "quality_gate.yaml": "gate_config_id",
}


class ConfigError(RuntimeError):
    """Raised when a config file is missing or malformed."""


def load_config(filename: str, config_dir: Path | None = None) -> dict[str, Any]:
    """Read one YAML config and validate its identity field."""
    path = (config_dir or CONFIG_DIR) / filename
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ConfigError(f"Config must be a mapping: {path}")

    id_field = _ID_FIELDS.get(filename)
    if id_field and not data.get(id_field):
        raise ConfigError(f"Config {filename} is missing required field '{id_field}'")

    return data


def active_config_ids(config_dir: Path | None = None) -> dict[str, str]:
    """Return the id of every known config — used by /admin/versions later."""
    ids: dict[str, str] = {}
    for filename, id_field in _ID_FIELDS.items():
        try:
            ids[filename] = str(load_config(filename, config_dir)[id_field])
        except ConfigError:
            ids[filename] = "missing"
    return ids
