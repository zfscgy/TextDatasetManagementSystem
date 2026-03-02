"""dms show [path] — List datasets or show a single dataset's metadata."""

from pathlib import Path
from typing import Optional

from dm.dataset import is_dataset_dir, load_dataset_config
from dm.root_config import get_dataset_root, resolve_dataset_path


def _collect_datasets(root: Path) -> list[Path]:
    """Recursively collect all dataset directories under root."""
    datasets = []
    if is_dataset_dir(root):
        datasets.append(root)
    else:
        for child in sorted(root.iterdir()):
            if child.is_dir():
                datasets.extend(_collect_datasets(child))
    return datasets


def _print_list(base: Path, datasets: list[Path], long: bool = False) -> None:
    """Print a compact listing of all datasets with name and sample keys.

    When long is True, also list individual JSONL filenames under each dataset.
    """
    for ds_path in datasets:
        rel = str(ds_path.relative_to(base.parent))
        cfg = load_dataset_config(ds_path)
        name: str = cfg.get("name") or ""
        sample_keys = list(cfg.get("format", {}).get("sample", {}).keys())
        name_part = f'  "{name}"' if name else ""
        keys_part = f"  {sample_keys}" if sample_keys else ""

        jsonl_files = sorted(f.name for f in ds_path.iterdir() if f.suffix.lower() == ".jsonl")
        count_part = f"  ({len(jsonl_files)} file{'s' if len(jsonl_files) != 1 else ''})"
        print(f"{rel}/{name_part}{keys_part}{count_part}")

        if long:
            if jsonl_files:
                for fname in jsonl_files:
                    print(f"  ├── {fname}")
            else:
                print("  └── (no JSONL files)")
    print(f"\nTotal: {len(datasets)} dataset(s)")


def _print_dataset(cfg: dict, rel_path: str) -> None:
    """Print full metadata for a single dataset."""
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
    path: Optional[str] = getattr(args, "path", None)
    long: bool = getattr(args, "long", False)

    if path:
        target = resolve_dataset_path(path)
        if not target.exists():
            raise SystemExit(f"Path not found: {path}")

        if is_dataset_dir(target):
            cfg = load_dataset_config(target)
            _print_dataset(cfg, path)
            return

        datasets = _collect_datasets(target)
        if not datasets:
            print(f"No datasets found under: {path}")
            return
        print(f"Datasets under: {target}\n")
        _print_list(target, datasets, long=long)
    else:
        root = get_dataset_root()
        datasets = _collect_datasets(root)
        if not datasets:
            print(f"No datasets found under: {root}")
            return
        print(f"Datasets under: {root}\n")
        _print_list(root, datasets, long=long)
