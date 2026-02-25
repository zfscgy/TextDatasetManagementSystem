"""dms add <dataset_path> <file_or_dir> — Add a JSONL/CSV file or folder to a dataset."""

from pathlib import Path

from dm.dataset import append_log, is_dataset_dir, load_dataset_config
from dm.root_config import resolve_dataset_path
from dm.validator import validate_file


def _add_single_file(src: Path, dataset_path: Path, fmt: dict) -> tuple[int, int]:
    """
    Validate and copy a single file into the dataset directory.
    Returns (valid_count, total_count). Returns (0, 0) and prints skip msg if unsupported.
    """
    suffix = src.suffix.lower()
    if suffix not in (".jsonl", ".csv"):
        print(f"  [SKIP] {src.name} — not a JSONL or CSV file")
        return 0, 0

    valid_lines, valid_count, total_count = validate_file(src, fmt)

    if suffix == ".csv":
        dest_name = src.stem + ".jsonl"
        print(f"  [CSV→JSONL] {src.name} → {dest_name}  ({valid_count}/{total_count} valid)")
    else:
        dest_name = src.name
        print(f"  [ADD] {src.name}  ({valid_count}/{total_count} valid)")

    dest = dataset_path / dest_name
    # If destination already exists, append rather than overwrite
    mode = "a" if dest.exists() else "w"
    with dest.open(mode, encoding="utf-8") as f:
        for line in valid_lines:
            f.write(line + "\n")

    return valid_count, total_count


def run(args) -> None:
    rel_path: str = args.dataset_path
    source: str = args.source

    dataset_path = resolve_dataset_path(rel_path)
    if not dataset_path.exists():
        raise SystemExit(f"Dataset not found: {dataset_path}")
    if not is_dataset_dir(dataset_path):
        raise SystemExit(f"'{rel_path}' is not a dataset (missing config.json)")

    cfg = load_dataset_config(dataset_path)
    fmt: dict = cfg.get("format", {})

    src_path = Path(source)
    if not src_path.exists():
        raise SystemExit(f"Source not found: {src_path}")

    files: list[Path] = []
    if src_path.is_file():
        files = [src_path]
    elif src_path.is_dir():
        files = [f for f in src_path.rglob("*") if f.is_file()]
    else:
        raise SystemExit(f"Source is neither a file nor a directory: {src_path}")

    total_valid = 0
    total_all = 0

    for f in sorted(files):
        v, t = _add_single_file(f, dataset_path, fmt)
        total_valid += v
        total_all += t

    print(f"\nSummary: {total_valid} valid / {total_all} total entries added.")

    append_log(dataset_path, f"add {rel_path} {source}")
