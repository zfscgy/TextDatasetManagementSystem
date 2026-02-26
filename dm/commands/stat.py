"""dms stat [folder] — Show tree-like statistics for datasets."""

import json
import math
import statistics
from pathlib import Path
from typing import Optional

from dm.dataset import DATASET_CONFIG_NAME, is_dataset_dir
from dm.root_config import get_dataset_root, resolve_dataset_path


def _entry_char_stats(jsonl_path: Path) -> tuple[int, float, float]:
    """
    Return (count, mean_chars, std_chars) for entries in a JSONL file.
    Each entry is converted to its string representation for length measurement.
    """
    lengths = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lengths.append(len(line))
    if not lengths:
        return 0, 0.0, 0.0
    mean = statistics.mean(lengths)
    std = statistics.pstdev(lengths) if len(lengths) > 1 else 0.0
    return len(lengths), mean, std


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


def _print_tree(base: Path, datasets: list[Path]) -> tuple[int, int]:
    """Print a tree-like view of all datasets and their JSONL files.

    Returns (total_datasets, total_entries) across all datasets.
    """
    total_entries = 0

    for ds_path in datasets:
        rel = ds_path.relative_to(base.parent)
        print(f"\n{rel}/")

        jsonl_files = sorted(
            [f for f in ds_path.iterdir() if f.suffix.lower() == ".jsonl"]
        )
        if not jsonl_files:
            print("  (no JSONL files)")
            continue

        ds_entries = 0
        ds_lengths: list[float] = []

        for jf in jsonl_files:
            count, mean, std = _entry_char_stats(jf)
            print(
                f"  ├── {jf.name}  "
                f"entries={count}  "
                f"avg_chars={mean:.1f}  "
                f"std={std:.1f}"
            )
            ds_entries += count
            ds_lengths.extend([mean] * count)

        ds_mean = statistics.mean(ds_lengths) if ds_lengths else 0.0
        ds_std = statistics.pstdev(ds_lengths) if len(ds_lengths) > 1 else 0.0
        print(
            f"  └── [total]  "
            f"entries={ds_entries}  "
            f"avg_chars={ds_mean:.1f}  "
            f"std={ds_std:.1f}"
        )
        total_entries += ds_entries

    return len(datasets), total_entries


def run(args) -> None:
    folder: Optional[str] = getattr(args, "folder", None)

    if folder:
        root = resolve_dataset_path(folder)
    else:
        root = get_dataset_root()

    if not root.exists():
        label = folder if folder else str(root)
        raise SystemExit(f"Path not found: {label}")

    datasets = _collect_datasets(root)

    if not datasets:
        print(f"No datasets found under: {root}")
        return

    print(f"Statistics for: {root}")
    total_datasets, total_entries = _print_tree(root, datasets)
    print(f"\nTotal: {total_datasets} dataset(s), {total_entries} entries")
