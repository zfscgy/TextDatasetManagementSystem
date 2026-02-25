"""dms update <dataset_path> — Update dataset metadata interactively."""

import json

from dm.dataset import append_log, load_dataset_config, save_dataset_config
from dm.root_config import resolve_dataset_path


def _prompt_with_default(prompt: str, default: str) -> str:
    """Show a prompt with a default value; return default if user enters nothing."""
    display = default if default else ""
    raw = input(f"{prompt} [{display}]: ").strip()
    return raw if raw else default


def _prompt_sample(current: dict) -> dict:
    """Prompt for a new sample JSON, defaulting to current."""
    current_str = json.dumps(current, ensure_ascii=False)
    print(f"Sample JSON [{current_str}]:")
    print("Enter new JSON or press Enter to keep current (end with blank line):")
    lines = []
    while True:
        line = input()
        if not line.strip():
            if not lines:
                return current
            combined = "\n".join(lines).strip()
            try:
                obj = json.loads(combined)
                if isinstance(obj, dict):
                    return obj
                print("Must be a JSON object. Try again.")
                lines = []
            except json.JSONDecodeError:
                print("Invalid JSON. Try again.")
                lines = []
        else:
            lines.append(line)
            combined = "\n".join(lines).strip()
            if combined.endswith("}"):
                try:
                    obj = json.loads(combined)
                    if isinstance(obj, dict):
                        return obj
                except json.JSONDecodeError:
                    pass


def run(args) -> None:
    rel_path: str = args.dataset_path
    dataset_path = resolve_dataset_path(rel_path)

    if not dataset_path.exists():
        raise SystemExit(f"Dataset not found: {dataset_path}")

    cfg = load_dataset_config(dataset_path)
    fmt: dict = cfg.get("format", {})
    current_sample: dict = fmt.get("sample", {})
    current_rc: list = fmt.get("required_columns", [])

    print(f"Updating dataset: {rel_path}")
    print("Press Enter to keep the current value shown in brackets.\n")

    # --- Sample ---
    new_sample = _prompt_sample(current_sample)

    # --- Required columns ---
    rc_display = ",".join(current_rc) if current_rc else "(all)"
    rc_input = _prompt_with_default(
        "Required columns (comma-separated, empty=all)", rc_display
    )
    if rc_input == "(all)" or not rc_input:
        new_rc = []
    else:
        new_rc = [c.strip() for c in rc_input.split(",") if c.strip()]
        invalid = [c for c in new_rc if c not in new_sample]
        if invalid:
            raise SystemExit(f"Required columns not in sample: {invalid}")

    # --- Optional metadata ---
    new_name = _prompt_with_default("Name", cfg.get("name", ""))
    new_description = _prompt_with_default("Description", cfg.get("description", ""))
    new_creator = _prompt_with_default("Creator", cfg.get("creator", ""))

    cfg["format"] = {"sample": new_sample, "required_columns": new_rc}
    cfg["name"] = new_name
    cfg["description"] = new_description
    cfg["creator"] = new_creator

    save_dataset_config(dataset_path, cfg)
    append_log(dataset_path, f"update {rel_path}")

    print(f"\nDataset '{rel_path}' updated successfully.")
