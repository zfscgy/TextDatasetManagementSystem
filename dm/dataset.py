"""Per-dataset config.json management."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

DATASET_CONFIG_NAME = "config.json"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def now_str() -> str:
    return datetime.now().strftime(TIMESTAMP_FORMAT)


def load_dataset_config(dataset_path: Path) -> dict:
    """Load and return the dataset config.json. Raises SystemExit if missing."""
    cfg_path = dataset_path / DATASET_CONFIG_NAME
    if not cfg_path.exists():
        raise SystemExit(f"Dataset config not found at: {cfg_path}")
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise SystemExit(f"Dataset config is corrupted: {e}")


def save_dataset_config(dataset_path: Path, cfg: dict) -> None:
    """Save dataset config to config.json, updating last_modify_time."""
    cfg["last_modify_time"] = now_str()
    cfg_path = dataset_path / DATASET_CONFIG_NAME
    with cfg_path.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def create_dataset_config(
    dataset_path: Path,
    fmt: dict,
    name: Optional[str] = None,
    description: Optional[str] = None,
    creator: Optional[str] = None,
    log_entry: Optional[str] = None,
) -> dict:
    """Create and write a new dataset config.json. Returns the config dict."""
    timestamp = now_str()
    cfg = {
        "created_time": timestamp,
        "last_modify_time": timestamp,
        "format": fmt,
        "name": name or "",
        "description": description or "",
        "creator": creator or "",
        "logs": [],
    }
    if log_entry:
        cfg["logs"].append(log_entry)
    dataset_path.mkdir(parents=True, exist_ok=True)
    cfg_path = dataset_path / DATASET_CONFIG_NAME
    with cfg_path.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    return cfg


def append_log(dataset_path: Path, command_str: str) -> None:
    """Append a log entry to the dataset config and save."""
    cfg = load_dataset_config(dataset_path)
    entry = f"[{now_str()}] dms {command_str}"
    cfg["logs"].append(entry)
    save_dataset_config(dataset_path, cfg)


def count_entries(jsonl_path: Path) -> int:
    """Count non-empty lines in a JSONL file."""
    count = 0
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def is_dataset_dir(path: Path) -> bool:
    """Return True if the given path looks like a dataset directory."""
    return (path / DATASET_CONFIG_NAME).exists()
