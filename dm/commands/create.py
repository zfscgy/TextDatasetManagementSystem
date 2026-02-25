"""dms create <dataset_path> — Create a new dataset."""

import json

from dm.dataset import create_dataset_config, now_str
from dm.root_config import resolve_dataset_path


def _prompt_sample() -> dict:
    """Interactively prompt the user to enter a JSON sample."""
    print("Enter a sample JSON object for this dataset.")
    print("Type or paste valid JSON (single line or multi-line).")
    print("End input with a blank line after the closing brace.\n")

    lines = []
    while True:
        line = input()
        lines.append(line)
        combined = "\n".join(lines).strip()
        # Try to parse incrementally once we have something that looks complete
        if combined.endswith("}") or combined.endswith("]"):
            try:
                obj = json.loads(combined)
                if isinstance(obj, dict):
                    return obj
                print("Sample must be a JSON object (dict). Try again.")
                lines = []
            except json.JSONDecodeError:
                pass  # keep reading lines
        if not line.strip() and combined:
            # Blank line — attempt to parse what we have
            try:
                obj = json.loads(combined)
                if isinstance(obj, dict):
                    return obj
                print("Sample must be a JSON object (dict). Try again.")
                lines = []
            except json.JSONDecodeError:
                print("Invalid JSON. Please try again.")
                lines = []


def run(args) -> None:
    rel_path: str = args.dataset_path
    dataset_path = resolve_dataset_path(rel_path)

    if dataset_path.exists():
        raise SystemExit(f"Dataset already exists: {dataset_path}")

    print(f"Creating dataset: {rel_path}\n")

    # --- Sample (required) ---
    sample = _prompt_sample()
    print(f"  Sample keys: {list(sample.keys())}")

    # --- Required columns ---
    all_keys = list(sample.keys())
    print(
        f"\nRequired columns (comma-separated). "
        f"Enter 'all' to require all columns {all_keys}, or leave empty for none: "
    )
    rc_input = input().strip().lower()
    if rc_input == "all":
        required_columns = all_keys
    elif rc_input:
        required_columns = [c.strip() for c in rc_input.split(",") if c.strip()]
        invalid = [c for c in required_columns if c not in sample]
        if invalid:
            raise SystemExit(f"Required columns not in sample: {invalid}")
    else:
        required_columns = []

    fmt = {"sample": sample, "required_columns": required_columns}

    # --- Optional fields ---
    name = input("\nName (optional): ").strip()
    description = input("Description (optional): ").strip()
    creator = input("Creator (optional): ").strip()

    log_entry = f"[{now_str()}] dms create {rel_path}"

    create_dataset_config(
        dataset_path,
        fmt=fmt,
        name=name or None,
        description=description or None,
        creator=creator or None,
        log_entry=log_entry,
    )

    print(f"\nDataset created at: {dataset_path}")
