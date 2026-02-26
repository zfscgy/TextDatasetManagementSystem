"""Root config.json management for the DatasetManager."""

import json
from pathlib import Path

ROOT_CONFIG_PATH = Path(__file__).parent.parent / "config.json"



def load_root_config() -> dict:
    """Load and return the root config. Auto-migrates legacy format. Raises SystemExit if missing."""
    if not ROOT_CONFIG_PATH.exists():
        raise SystemExit(
            "Root config.json not found. Run 'dms init' first to initialize the system."
        )
    try:
        with ROOT_CONFIG_PATH.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
    except json.JSONDecodeError as e:
        raise SystemExit(f"Root config.json is corrupted: {e}")

    if "active" not in cfg or "configs" not in cfg:
        raise SystemExit(
            "Root config.json is missing required structure. Run 'dms init' to reinitialize."
        )
    return cfg


def save_root_config(cfg: dict) -> None:
    """Save root config to config.json."""
    with ROOT_CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def get_active_config_name() -> str:
    """Return the name of the currently active config."""
    return load_root_config()["active"]


def get_active_config() -> dict:
    """Return the active config entry dict (contains dataset_root and recovery)."""
    cfg = load_root_config()
    active = cfg["active"]
    if active not in cfg["configs"]:
        raise SystemExit(
            f"Active config '{active}' not found in configs. Run 'dms init' to reinitialize."
        )
    entry = cfg["configs"][active]
    for key in ("dataset_root", "recovery"):
        if key not in entry:
            raise SystemExit(f"Active config '{active}' is missing required key: '{key}'.")
    return entry


def get_dataset_root() -> Path:
    return Path(get_active_config()["dataset_root"])


def get_recovery_root() -> Path:
    return Path(get_active_config()["recovery"])


def resolve_dataset_path(relative_path: str) -> Path:
    """Resolve a dataset relative path (e.g. 'test/d1') to an absolute path."""
    return get_dataset_root() / relative_path
