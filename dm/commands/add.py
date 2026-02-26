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


def _suffixed_name(dataset_path: Path, stem: str, ext: str, used: set[str]) -> str:
    """Return a name with _1, _2, … suffix that is free both on disk and in `used`.

    Only called for within-run duplicates (where the natural name is already
    claimed by an earlier file in the same batch).
    """
    i = 1
    while True:
        candidate = f"{stem}_{i}{ext}"
        if candidate not in used and not (dataset_path / candidate).exists():
            return candidate
        i += 1


def _add_single_file(
    src: Path,
    dataset_path: Path,
    fmt: dict,
    mappings: list[tuple[list[str], list[str]]],
    used: set[str],
) -> tuple[int, int]:
    """Validate and copy a single file into the dataset directory.

    Conflict resolution:
    - Natural name already claimed in this run → auto-suffix (_1, _2, …).
    - Natural name exists on disk from a previous run → prompt overwrite/skip.
    """
    suffix = src.suffix.lower()
    if suffix not in (".jsonl", ".json", ".csv"):
        print(f"  [SKIP] {src.name} — not a JSONL, JSON, or CSV file")
        return 0, 0

    result = validate_file(src, fmt, mappings)
    if isinstance(result, str):
        print(f"  [ERROR] {src.name} — {result}")
        return 0, 0
    valid_lines, valid_count, total_count, top_reason = result

    if valid_count == 0:
        msg = f"  [SKIP] {src.name} — no valid entries ({total_count} total), file not written."
        if top_reason:
            msg += f"\n    reason: {top_reason}"
        print(msg)
        return 0, total_count

    dest_ext = ".jsonl"
    dest_stem = src.stem
    label = "CSV→JSONL" if suffix == ".csv" else ("JSON→JSONL" if suffix == ".json" else "ADD")
    natural_name = dest_stem + dest_ext

    if natural_name in used:
        # Within-run duplicate → auto-suffix, no prompt needed
        dest_name = _suffixed_name(dataset_path, dest_stem, dest_ext, used)
    elif (dataset_path / natural_name).exists():
        # Exists from a previous run → ask the user
        choice = input(f"  '{natural_name}' already exists. [o]verwrite / [s]kip? ").strip().lower()
        if choice != "o":
            print(f"  [SKIP] {src.name} — skipped.")
            return 0, 0
        dest_name = natural_name
    else:
        dest_name = natural_name

    used.add(dest_name)

    if dest_name != natural_name or suffix in (".csv", ".json"):
        print(f"  [{label}] {src.name} → {dest_name}  ({valid_count}/{total_count} valid)")
    else:
        print(f"  [{label}] {src.name}  ({valid_count}/{total_count} valid)")
    if top_reason and valid_count < total_count:
        print(f"    top rejection reason: {top_reason}")

    dest = dataset_path / dest_name
    with dest.open("w", encoding="utf-8") as f:
        for line in valid_lines:
            f.write(line + "\n")

    return valid_count, total_count


def run(args) -> None:
    rel_path: str = args.dataset_path
    source: str = args.source
    mappings = _parse_mappings(args.column_map)

    dataset_path = resolve_dataset_path(rel_path)
    if not dataset_path.exists():
        raise SystemExit(f"Dataset not found: {rel_path}")
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
        files = sorted(f for f in src_path.rglob("*") if f.is_file())
        if not files:
            raise SystemExit(f"No files found under: {src_path}")
        print(f"Found {len(files)} file(s) under {src_path}")
    else:
        raise SystemExit(f"Source is neither a file nor a directory: {src_path}")

    if mappings:
        specs = ", ".join(f"{'.'.join(s)}:{'.'.join(d)}" for s, d in mappings)
        print(f"  Column mappings: {specs}")

    used: set[str] = set()
    total_valid = 0
    total_all = 0

    for f in files:
        v, t = _add_single_file(f, dataset_path, fmt, mappings, used)
        total_valid += v
        total_all += t

    print(f"\nSummary: {total_valid} valid / {total_all} total entries added.")

    mapping_str = (" " + " ".join(f"-c {spec}" for spec in (args.column_map or []))) if args.column_map else ""
    append_log(dataset_path, f"add {rel_path} {source}{mapping_str}")
