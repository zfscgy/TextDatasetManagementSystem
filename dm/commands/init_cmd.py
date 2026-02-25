"""dms init — Initialize the Dataset Management System."""

import json
from pathlib import Path

from dm.root_config import ROOT_CONFIG_PATH, save_root_config


def run(args) -> None:
    if ROOT_CONFIG_PATH.exists():
        print(f"Root config already exists at: {ROOT_CONFIG_PATH}")
        overwrite = input("Overwrite? [y/N]: ").strip().lower()
        if overwrite != "y":
            print("Aborted.")
            return

    print("Initialize the Dataset Management System.")
    print("Press Enter to accept the default value shown in brackets.\n")

    default_root = str(Path.home() / "datasets")
    default_recovery = str(Path.home() / "datasets" / ".recovery")

    dataset_root = input(f"Dataset root directory [{default_root}]: ").strip()
    if not dataset_root:
        dataset_root = default_root

    recovery = input(f"Recovery directory [{default_recovery}]: ").strip()
    if not recovery:
        recovery = default_recovery

    root_path = Path(dataset_root)
    recovery_path = Path(recovery)

    root_path.mkdir(parents=True, exist_ok=True)
    recovery_path.mkdir(parents=True, exist_ok=True)

    cfg = {
        "dataset_root": str(root_path),
        "recovery": str(recovery_path),
    }
    save_root_config(cfg)

    print(f"\nInitialized successfully.")
    print(f"  Dataset root : {root_path}")
    print(f"  Recovery     : {recovery_path}")
    print(f"  Config saved : {ROOT_CONFIG_PATH}")
