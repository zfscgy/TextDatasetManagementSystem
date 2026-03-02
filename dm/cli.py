"""dms — Dataset Management System CLI."""

import argparse
import sys

from dm.commands import add, config_cmd, create, export_cmd, import_cmd, init_cmd, mv, prune, rm, show, stat, update


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dms",
        description="Dataset Management System — manage large-scale text datasets in JSONL format.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── init ─────────────────────────────────────────────────────────────────
    sub.add_parser("init", help="Initialize the Dataset Management System")

    # ── config ───────────────────────────────────────────────────────────────
    p_config = sub.add_parser("config", help="Show or manage root configurations")
    config_sub = p_config.add_subparsers(dest="config_subcommand", metavar="<subcommand>")
    p_config_add = config_sub.add_parser("add", help="Add a new named configuration")
    p_config_add.add_argument("name", help="Configuration name, e.g. 'work'")

    # ── create ───────────────────────────────────────────────────────────────
    p_create = sub.add_parser("create", help="Create a new dataset")
    p_create.add_argument("dataset_path", help="Relative dataset path, e.g. test/d1")

    # ── add ──────────────────────────────────────────────────────────────────
    p_add = sub.add_parser("add", help="Add a JSONL/CSV file or folder to a dataset")
    p_add.add_argument("dataset_path", help="Relative dataset path, e.g. test/d1")
    p_add.add_argument("source", help="Source file or directory to add")
    p_add.add_argument(
        "-c", "--column-map",
        dest="column_map",
        metavar="SRC:DST",
        action="append",
        help=(
            "Rename a column before validation. "
            "Use dot notation for nested keys, e.g. -c messages.from:messages.role. "
            "Can be specified multiple times."
        ),
    )

    # ── rm ───────────────────────────────────────────────────────────────────
    p_rm = sub.add_parser("rm", help="Remove a JSONL file from a dataset")
    p_rm.add_argument("dataset_path", help="Relative dataset path, e.g. test/d1")
    p_rm.add_argument("filename", help="JSONL filename to remove, e.g. a.jsonl")

    # ── mv ───────────────────────────────────────────────────────────────────
    p_mv = sub.add_parser("mv", help="Rename a dataset")
    p_mv.add_argument("dataset_path", help="Current relative dataset path")
    p_mv.add_argument("new_path", help="New relative dataset path")

    # ── update ───────────────────────────────────────────────────────────────
    p_update = sub.add_parser("update", help="Update dataset metadata")
    p_update.add_argument("dataset_path", help="Relative dataset path, e.g. test/d1")

    # ── stat ─────────────────────────────────────────────────────────────────
    p_stat = sub.add_parser("stat", help="Show statistics for datasets")
    p_stat.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="Relative folder path to inspect (default: entire dataset root)",
    )

    # ── export ───────────────────────────────────────────────────────────────
    p_export = sub.add_parser("export", help="Export datasets to a zip file")
    p_export.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="Relative folder to export (default: entire dataset root)",
    )
    p_export.add_argument(
        "-o", "--output", required=True, metavar="FILE.zip", help="Output zip file path"
    )

    # ── import ───────────────────────────────────────────────────────────────
    p_import = sub.add_parser("import", help="Import datasets from a zip file")
    p_import.add_argument("zip_file", help="Path to the zip file to import")
    p_import.add_argument(
        "-o", "--output", required=True, metavar="FOLDER", help="Destination relative folder path"
    )

    # ── show ─────────────────────────────────────────────────────────────────
    p_show = sub.add_parser("show", help="List datasets or show a single dataset's metadata")
    p_show.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Relative path to inspect — a dataset for full metadata, a folder for listing (default: entire dataset root)",
    )
    p_show.add_argument(
        "-l",
        action="store_true",
        dest="long",
        help="Also list individual JSONL filenames under each dataset",
    )

    # ── prune ────────────────────────────────────────────────────────────────
    p_prune = sub.add_parser(
        "prune", help="Remove extra columns from dataset JSONL files"
    )
    prune_group = p_prune.add_mutually_exclusive_group(required=True)
    prune_group.add_argument(
        "dataset_path",
        nargs="?",
        default=None,
        help="Relative dataset path to prune, e.g. test/d1",
    )
    prune_group.add_argument(
        "-a", "--all",
        action="store_true",
        dest="all",
        help="Prune all datasets",
    )

    return parser


COMMAND_MAP = {
    "init": init_cmd.run,
    "config": config_cmd.run,
    "create": create.run,
    "add": add.run,
    "rm": rm.run,
    "mv": mv.run,
    "update": update.run,
    "stat": stat.run,
    "export": export_cmd.run,
    "import": import_cmd.run,
    "prune": prune.run,
    "show": show.run,
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    handler = COMMAND_MAP[args.command]
    try:
        handler(args)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)
