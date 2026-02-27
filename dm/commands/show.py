"""dms show dataset <dataset_path> — Show dataset metadata from config.json."""

import json

from dm.dataset import is_dataset_dir, load_dataset_config
from dm.root_config import resolve_dataset_path


def _print_dataset(cfg: dict, rel_path: str) -> None:
    print(f"Dataset : {rel_path}")
    print(f"  Name         : {cfg.get('name') or '(not set)'}")
    print(f"  Description  : {cfg.get('description') or '(not set)'}")
    print(f"  Creator      : {cfg.get('creator') or '(not set)'}")
    print(f"  Created      : {cfg.get('created_time', '(unknown)')}")
    print(f"  Last modified: {cfg.get('last_modify_time', '(unknown)')}")

    fmt: dict = cfg.get("format", {})
    sample: dict = fmt.get("sample", {})
    required: list = fmt.get("required_columns", [])

    print(f"\n  Format:")
    if sample:
        print(f"    Sample keys      : {list(sample.keys())}")
        print(f"    Required columns : {required if required else '(none)'}")
    else:
        print("    (no format defined)")

    logs: list = cfg.get("logs", [])
    print(f"\n  Logs ({len(logs)} entr{'y' if len(logs) == 1 else 'ies'}):")
    if logs:
        for entry in logs:
            print(f"    {entry}")
    else:
        print("    (no log entries)")


def run(args) -> None:
    subcommand = getattr(args, "show_subcommand", None)

    if subcommand == "dataset":
        rel_path: str = args.dataset_path
        dataset_path = resolve_dataset_path(rel_path)

        if not dataset_path.exists():
            raise SystemExit(f"Dataset not found: {rel_path}")
        if not is_dataset_dir(dataset_path):
            raise SystemExit(f"'{rel_path}' is not a dataset (missing config.json)")

        cfg = load_dataset_config(dataset_path)
        _print_dataset(cfg, rel_path)
    else:
        raise SystemExit("Usage: dms show dataset <dataset_path>")
