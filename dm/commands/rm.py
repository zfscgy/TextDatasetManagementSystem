"""dms rm <dataset_path> <filename> — Remove a JSONL file from the dataset."""

import shutil
from pathlib import Path

from dm.dataset import append_log, count_entries, load_dataset_config
from dm.root_config import get_recovery_root, resolve_dataset_path


def run(args) -> None:
    rel_path: str = args.dataset_path
    filename: str = args.filename

    dataset_path = resolve_dataset_path(rel_path)
    if not dataset_path.exists():
        raise SystemExit(f"Dataset not found: {rel_path}")

    target = dataset_path / filename
    if not target.exists():
        raise SystemExit(f"File not found in dataset '{rel_path}': {filename}")

    if target.suffix.lower() != ".jsonl":
        raise SystemExit(f"Only JSONL files can be removed. Got: {filename}")

    entry_count = count_entries(target)

    # Mirror the dataset relative path in the recovery folder
    recovery_root = get_recovery_root()
    recovery_dest_dir = recovery_root / rel_path
    recovery_dest_dir.mkdir(parents=True, exist_ok=True)
    recovery_dest = recovery_dest_dir / filename

    # If a file with the same name already exists in recovery, add a suffix
    if recovery_dest.exists():
        stem = target.stem
        suffix = target.suffix
        counter = 1
        while recovery_dest.exists():
            recovery_dest = recovery_dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    shutil.move(str(target), str(recovery_dest))

    print(f"Removed '{filename}' from dataset '{rel_path}'.")
    print(f"  Entries removed : {entry_count}")
    print(f"  Moved to        : {recovery_dest}")

    append_log(dataset_path, f"rm {rel_path} {filename}")
