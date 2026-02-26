"""dms config [add <name>] — Show or manage root configurations."""

from pathlib import Path

from dm.root_config import load_root_config, save_root_config


def _print_config(cfg: dict) -> None:
    active = cfg["active"]
    configs = cfg.get("configs", {})
    print(f"Active config : {active}")
    print(f"All configs   : {', '.join(configs.keys()) if configs else '(none)'}\n")
    entry = configs.get(active, {})
    print(f"  dataset_root : {entry.get('dataset_root', '(not set)')}")
    print(f"  recovery     : {entry.get('recovery', '(not set)')}")


def run(args) -> None:
    subcommand = getattr(args, "config_subcommand", None)

    if subcommand == "add":
        cfg = load_root_config()
        name: str = args.name

        if name in cfg["configs"]:
            overwrite = input(f"Config '{name}' already exists. Overwrite? [y/N]: ").strip().lower()
            if overwrite != "y":
                print("Aborted.")
                return

        print(f"Adding config: {name}")
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

        cfg["configs"][name] = {
            "dataset_root": str(root_path),
            "recovery": str(recovery_path),
        }
        save_root_config(cfg)

        print(f"\nConfig '{name}' added.")
        print(f"  dataset_root : {root_path}")
        print(f"  recovery     : {recovery_path}")

    else:
        _print_config(load_root_config())
