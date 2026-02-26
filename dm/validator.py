"""JSONL/CSV validation logic against a dataset format."""

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Iterator, List, Tuple

from dm.mapper import apply_mappings


# BOMs that Python's codec names handle transparently
_BOM_MAP: list[tuple[bytes, str]] = [
    (b"\x00\x00\xfe\xff", "utf-32-be"),
    (b"\xff\xfe\x00\x00", "utf-32-le"),
    (b"\xfe\xff", "utf-16-be"),
    (b"\xff\xfe", "utf-16-le"),
    (b"\xef\xbb\xbf", "utf-8-sig"),  # UTF-8 with BOM
]


def detect_encoding(path: Path) -> str:
    """Return the most likely text encoding for *path*.

    Strategy:
    1. Check for a leading BOM (covers UTF-8 BOM, UTF-16, UTF-32).
    2. Ask ``charset_normalizer`` for a best guess from the raw bytes.
    3. Fall back to ``utf-8``.
    """
    with path.open("rb") as fh:
        raw = fh.read()

    for bom, enc in _BOM_MAP:
        if raw.startswith(bom):
            return enc

    try:
        from charset_normalizer import from_bytes

        result = from_bytes(raw).best()
        if result is not None:
            return str(result.encoding)
    except ImportError:
        pass

    return "utf-8"


def _check_dict_item(item: dict, sample_item: dict) -> bool:
    """Every key present in sample_item must exist in item with a matching type."""
    for key, sample_sub in sample_item.items():
        if key not in item:
            return False
        if not isinstance(item[key], type(sample_sub)):
            return False
        if isinstance(sample_sub, dict) and not _check_dict_item(item[key], sample_sub):
            return False
    return True


def _check_value_reason(val, sample_val, col: str, required: bool) -> str | None:
    """Return a rejection reason string, or None if the value is valid."""
    if val is None:
        return f"column '{col}' is None (required)" if required else None

    expected_type = type(sample_val)
    if not isinstance(val, expected_type):
        return (
            f"wrong type for '{col}' "
            f"(expected {expected_type.__name__}, got {type(val).__name__})"
        )

    if isinstance(sample_val, dict):
        if not _check_dict_item(val, sample_val):
            return f"invalid structure in '{col}'"
    elif isinstance(sample_val, list):
        if required and len(val) == 0:
            return f"empty required column '{col}'"
        if sample_val:
            sample_item = sample_val[0]
            item_type = type(sample_item)
            for item in val:
                if not isinstance(item, item_type):
                    return f"invalid item type in '{col}'"
                if isinstance(sample_item, dict) and not _check_dict_item(item, sample_item):
                    return f"invalid item structure in '{col}'"
    elif isinstance(sample_val, str):
        if required and val == "":
            return f"empty required column '{col}'"

    return None


def _check_value(val, sample_val, col: str, required: bool) -> bool:
    return _check_value_reason(val, sample_val, col, required) is None


def validate_line_reason(obj: dict, fmt: dict) -> str | None:
    """Return None if obj is valid, or a human-readable rejection reason."""
    if not isinstance(obj, dict):
        return "not a JSON object"

    sample: dict = fmt.get("sample", {})
    required_columns: List[str] = fmt.get("required_columns", [])
    required_set = set(required_columns)

    for key, sample_val in sample.items():
        if key not in obj:
            if key in required_set:
                return f"missing required column '{key}'"
            continue
        reason = _check_value_reason(obj[key], sample_val, key, required=key in required_set)
        if reason:
            return reason

    return None


def validate_line(obj: dict, fmt: dict) -> bool:
    """Return True if obj passes format validation."""
    return validate_line_reason(obj, fmt) is None


def iter_jsonl(path: Path) -> Iterator[Tuple[int, dict, bool]]:
    """
    Yield (line_number, parsed_obj, is_valid_json) for each non-empty line.
    is_valid_json is False if the line couldn't be parsed.
    """
    with path.open("r", encoding=detect_encoding(path)) as f:
        for lineno, raw in enumerate(f, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                yield lineno, obj, True
            except json.JSONDecodeError:
                yield lineno, {}, False


def csv_to_jsonl_lines(path: Path) -> List[str]:
    """Convert a CSV file to a list of JSON strings (one per row)."""
    lines = []
    with path.open("r", encoding=detect_encoding(path), newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lines.append(json.dumps(dict(row), ensure_ascii=False))
    return lines


def json_to_jsonl_lines(path: Path) -> List[str]:
    """
    Read a JSON file containing a list of objects and return one JSON string per entry.
    Raises ValueError if the file is not a JSON list.
    """
    with path.open("r", encoding=detect_encoding(path)) as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"'{path.name}' is a JSON file but does not contain a list")
    return [json.dumps(item, ensure_ascii=False) for item in data]


def validate_file(
    path: Path,
    fmt: dict,
    mappings: List[Tuple[List[str], List[str]]] | None = None,
) -> Tuple[List[str], int, int, str | None] | str:
    """
    Validate a JSONL, JSON, or CSV file against fmt.
    If mappings are provided, each row is renamed before validation.

    Returns:
        (valid_lines, valid_count, total_count, top_reason)  on success
            top_reason is the most common rejection reason, or None if all entries are valid.
        str (error message)  if the file should be skipped with an error
    """
    suffix = path.suffix.lower()
    raw_lines: List[str] = []

    if suffix == ".csv":
        raw_lines = csv_to_jsonl_lines(path)
    elif suffix == ".jsonl":
        with path.open("r", encoding=detect_encoding(path)) as f:
            raw_lines = [ln.strip() for ln in f if ln.strip()]
    elif suffix == ".json":
        try:
            raw_lines = json_to_jsonl_lines(path)
        except ValueError as e:
            return str(e)
    else:
        return [], 0, 0, None

    valid_lines: List[str] = []
    reasons: Counter = Counter()

    for raw in raw_lines:
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            reasons["invalid JSON"] += 1
            continue
        try:
            if mappings:
                apply_mappings(obj, mappings)
            reason = validate_line_reason(obj, fmt)
            if reason is None:
                valid_lines.append(json.dumps(obj, ensure_ascii=False))
            else:
                reasons[reason] += 1
        except Exception:
            reasons["unexpected error during mapping"] += 1

    top_reason = reasons.most_common(1)[0][0] if reasons else None
    return valid_lines, len(valid_lines), len(raw_lines), top_reason
