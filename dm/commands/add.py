"""dms add <dataset_path> <file_or_dir> — Add a JSONL/CSV file or folder to a dataset."""

from pathlib import Path

from dm.dataset import append_log, is_dataset_dir, load_dataset_config
from dm.mapper import apply_mappings, parse_mapping
from dm.root_config import resolve_dataset_path
from dm.validator import validate_file


def _parse_mappings(column_map: list[str]) -> list[tuple[list[str], list[str]]]:
    """Parse and validate all -c specs. Raises SystemExit on bad input."""
    mappings = []
    for spec in column_map or []:
        try:
            mappings.append(parse_mapping(spec))
        except ValueError as e:
            raise SystemExit(str(e))
    return mappings


def _add_single_file(
    src: Path,
    dataset_path: Path,
    fmt: dict,
    mappings: list[tuple[list[str], list[str]]],
) -> tuple[int, int]:
    """
    Validate and copy a single file into the dataset directory.
    Column mappings are applied before validation.
    Returns (valid_count, total_count). Returns (0, 0) and prints skip msg if unsupported.
    """
    suffix = src.suffix.lower()
    if suffix not in (".jsonl", ".json", ".csv"):
        print(f"  [SKIP] {src.name} — not a JSONL, JSON, or CSV file")
        return 0, 0

    result = validate_file(src, fmt, mappings)
    if isinstance(result, str):
        print(f"  [ERROR] {src.name} — {result}")
        return 0, 0
    valid_lines, valid_count, total_count = result

    if suffix in (".csv", ".json"):
        dest_name = src.stem + ".jsonl"
        label = "CSV→JSONL" if suffix == ".csv" else "JSON→JSONL"
        print(f"  [{label}] {src.name} → {dest_name}  ({valid_count}/{total_count} valid)")
    else:
        dest_name = src.name
        print(f"  [ADD] {src.name}  ({valid_count}/{total_count} valid)")

    if valid_count == 0:
        print(f"    [SKIP] No valid entries, file not written.")
        return 0, total_count

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
    mappings = _parse_mappings(args.column_map)

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

    if mappings:
        specs = ", ".join(f"{'.'.join(s)}:{'.'.join(d)}" for s, d in mappings)
        print(f"  Column mappings: {specs}")

    total_valid = 0
    total_all = 0

    for f in sorted(files):
        v, t = _add_single_file(f, dataset_path, fmt, mappings)
        total_valid += v
        total_all += t

    print(f"\nSummary: {total_valid} valid / {total_all} total entries added.")

    mapping_str = (" " + " ".join(f"-c {spec}" for spec in (args.column_map or []))) if args.column_map else ""
    append_log(dataset_path, f"add {rel_path} {source}{mapping_str}")
