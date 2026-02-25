"""JSONL/CSV validation logic against a dataset format."""

import csv
import io
import json
from pathlib import Path
from typing import Iterator, List, Tuple


def validate_line(obj: dict, fmt: dict) -> bool:
    """
    Return True if obj passes the format validation:
    - All keys from format sample must be present.
    - All required_columns must be present and non-empty strings.
    """
    sample: dict = fmt.get("sample", {})
    required_columns: List[str] = fmt.get("required_columns", [])

    # All columns must be all if required_columns is empty
    if not required_columns:
        required_columns = list(sample.keys())

    for col in required_columns:
        val = obj.get(col)
        if val is None:
            return False
        if isinstance(val, str) and val == "":
            return False

    # All keys present in the sample must exist in obj
    for key in sample:
        if key not in obj:
            return False

    return True


def iter_jsonl(path: Path) -> Iterator[Tuple[int, dict, bool]]:
    """
    Yield (line_number, parsed_obj, is_valid_json) for each non-empty line.
    is_valid_json is False if the line couldn't be parsed.
    """
    with path.open("r", encoding="utf-8") as f:
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
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lines.append(json.dumps(dict(row), ensure_ascii=False))
    return lines


def validate_file(
    path: Path, fmt: dict
) -> Tuple[List[str], int, int]:
    """
    Validate a JSONL (or CSV) file against fmt.

    Returns:
        (valid_lines, valid_count, total_count)
        valid_lines: list of JSON strings that passed validation
    """
    suffix = path.suffix.lower()
    raw_lines: List[str] = []

    if suffix == ".csv":
        raw_lines = csv_to_jsonl_lines(path)
    elif suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            raw_lines = [ln.strip() for ln in f if ln.strip()]
    else:
        return [], 0, 0

    valid_lines = []
    total = len(raw_lines)

    for raw in raw_lines:
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if validate_line(obj, fmt):
            valid_lines.append(json.dumps(obj, ensure_ascii=False))

    return valid_lines, len(valid_lines), total
