"""dms prune <dataset_path> | -a — Remove extra columns from dataset JSONL files."""

import json
from pathlib import Path

from dm.dataset import append_log, is_dataset_dir, load_dataset_config
from dm.root_config import get_dataset_root, resolve_dataset_path
from dm.validator import detect_encoding


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


def _prune_file(jsonl_path: Path, allowed_keys: set[str]) -> tuple[int, int]:
    """Rewrite a JSONL file keeping only allowed top-level keys.

    Returns (entries_processed, columns_removed_total).
    """
    encoding = detect_encoding(jsonl_path)
    lines_out: list[str] = []
    columns_removed = 0

    with jsonl_path.open("r", encoding=encoding) as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                lines_out.append(raw)
                continue

            if not isinstance(obj, dict):
                lines_out.append(raw)
                continue

            extra = set(obj.keys()) - allowed_keys
            if extra:
                for key in extra:
                    del obj[key]
                columns_removed += len(extra)

            lines_out.append(json.dumps(obj, ensure_ascii=False))

    with jsonl_path.open("w", encoding="utf-8") as f:
        for line in lines_out:
            f.write(line + "\n")

    return len(lines_out), columns_removed


def _prune_dataset(dataset_path: Path, rel_label: str) -> None:
    """Prune all JSONL files in a single dataset directory."""
    cfg = load_dataset_config(dataset_path)
    sample: dict = cfg.get("format", {}).get("sample", {})

    if not sample:
        print(f"  [SKIP] {rel_label} — no format sample defined, nothing to prune.")
        return

    allowed_keys = set(sample.keys())
    jsonl_files = sorted(f for f in dataset_path.iterdir() if f.suffix.lower() == ".jsonl")

    if not jsonl_files:
        print(f"  [SKIP] {rel_label} — no JSONL files.")
        return

    total_entries = 0
    total_removed = 0

    for jf in jsonl_files:
        entries, removed = _prune_file(jf, allowed_keys)
        total_entries += entries
        total_removed += removed
        if removed:
            print(f"    {jf.name}: {entries} entries, {removed} extra column(s) removed")
        else:
            print(f"    {jf.name}: {entries} entries, already clean")

    print(
        f"  [{rel_label}] pruned {total_entries} entries, "
        f"{total_removed} extra column value(s) removed across {len(jsonl_files)} file(s)."
    )
    append_log(dataset_path, f"prune {rel_label}")


def run(args) -> None:
    prune_all: bool = getattr(args, "all", False)

    if prune_all:
        root = get_dataset_root()
        datasets = _collect_datasets(root)
        if not datasets:
            raise SystemExit(f"No datasets found under: {root}")
        print(f"Pruning {len(datasets)} dataset(s) under {root}\n")
        for ds_path in datasets:
            rel_label = str(ds_path.relative_to(root))
            _prune_dataset(ds_path, rel_label)
    else:
        rel_path: str = args.dataset_path
        dataset_path = resolve_dataset_path(rel_path)
        if not dataset_path.exists():
            raise SystemExit(f"Dataset not found: {rel_path}")
        if not is_dataset_dir(dataset_path):
            raise SystemExit(f"'{rel_path}' is not a dataset (missing config.json)")
        print(f"Pruning dataset: {rel_path}\n")
        _prune_dataset(dataset_path, rel_path)
