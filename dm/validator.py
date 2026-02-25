"""JSONL/CSV validation logic against a dataset format."""

import csv
import json
from pathlib import Path
from typing import Iterator, List, Tuple

from dm.mapper import apply_mappings


def _check_dict_item(item: dict, sample_item: dict) -> bool:
    """
    Validate a dict item against a sample dict item.
    Every key present in sample_item must exist in item with a matching type.
    """
    for key, sample_sub in sample_item.items():
        if key not in item:
            return False
        if not isinstance(item[key], type(sample_sub)):
            return False
        # Recurse into nested dicts
        if isinstance(sample_sub, dict) and not _check_dict_item(item[key], sample_sub):
            return False
    return True


def _check_value(val, sample_val, col: str, required: bool) -> bool:
    """
    Validate a single column value against the sample value for that column.

    Rules:
    - Type must match the sample value's type.
    - For required columns:
        - str: must be non-empty.
        - list: must be non-empty.
    - For list columns: every item must match the type of items in the sample list.
      If the sample list items are dicts, each item's keys and types are checked recursively.
    """
    expected_type = type(sample_val)

    if not isinstance(val, expected_type):
        return False

    if isinstance(sample_val, dict):
        if not _check_dict_item(val, sample_val):
            return False
    elif isinstance(sample_val, list):
        if required and len(val) == 0:
            return False
        if sample_val:
            sample_item = sample_val[0]
            item_type = type(sample_item)
            for item in val:
                if not isinstance(item, item_type):
                    return False
                if isinstance(sample_item, dict) and not _check_dict_item(item, sample_item):
                    return False
    elif isinstance(sample_val, str):
        if required and val == "":
            return False

    return True


def validate_line(obj: dict, fmt: dict) -> bool:
    """
    Return True if obj passes the format validation:
    - obj must be a JSON object (dict).
    - All keys from format sample must be present in obj.
    - Each column value must match the type defined by the sample.
    - For required columns: strings must be non-empty, lists must be non-empty,
      and list items must match the sample item type.
    """
    if not isinstance(obj, dict):
        return False

    sample: dict = fmt.get("sample", {})
    required_columns: List[str] = fmt.get("required_columns", [])
    required_set = set(required_columns)

    for key, sample_val in sample.items():
        if key not in obj:
            # Required columns must be present; optional ones can be omitted
            if key in required_set:
                return False
            continue
        val = obj[key]
        if not _check_value(val, sample_val, key, required=key in required_set):
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


def json_to_jsonl_lines(path: Path) -> List[str]:
    """
    Read a JSON file containing a list of objects and return one JSON string per entry.
    Raises ValueError if the file is not a JSON list.
    """
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"'{path.name}' is a JSON file but does not contain a list")
    return [json.dumps(item, ensure_ascii=False) for item in data]


def validate_file(
    path: Path,
    fmt: dict,
    mappings: List[Tuple[List[str], List[str]]] | None = None,
) -> Tuple[List[str], int, int] | str:
    """
    Validate a JSONL, JSON, or CSV file against fmt.
    If mappings are provided, each row is renamed before validation.

    Returns:
        (valid_lines, valid_count, total_count)  on success
        str (error message)                       if the file should be skipped with an error
    """
    suffix = path.suffix.lower()
    raw_lines: List[str] = []

    if suffix == ".csv":
        raw_lines = csv_to_jsonl_lines(path)
    elif suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            raw_lines = [ln.strip() for ln in f if ln.strip()]
    elif suffix == ".json":
        try:
            raw_lines = json_to_jsonl_lines(path)
        except ValueError as e:
            return str(e)
    else:
        return [], 0, 0

    valid_lines = []
    total = len(raw_lines)

    for raw in raw_lines:
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        try:
            if mappings:
                apply_mappings(obj, mappings)
            if validate_line(obj, fmt):
                valid_lines.append(json.dumps(obj, ensure_ascii=False))
        except Exception:
            continue

    return valid_lines, len(valid_lines), total
