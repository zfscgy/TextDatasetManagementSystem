"""dms mv <dataset_path> <new_path> — Rename a dataset."""

import shutil

from dm.dataset import append_log, load_dataset_config
from dm.root_config import resolve_dataset_path


def run(args) -> None:
    old_rel: str = args.dataset_path
    new_rel: str = args.new_path

    old_path = resolve_dataset_path(old_rel)
    new_path = resolve_dataset_path(new_rel)

    if not old_path.exists():
        raise SystemExit(f"Dataset not found: {old_rel}")

    if new_path.exists():
        raise SystemExit(f"Destination already exists: {new_rel}")

    # Ensure parent directory of destination exists
    new_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.move(str(old_path), str(new_path))

    print(f"Renamed dataset:")
    print(f"  From : {old_rel}  ({old_path})")
    print(f"  To   : {new_rel}  ({new_path})")

    # Log the operation under the new location
    append_log(new_path, f"mv {old_rel} {new_rel}")
