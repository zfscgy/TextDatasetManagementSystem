"""dms export [folder] -o <output.zip> — Export datasets to a zip file."""

import zipfile
from pathlib import Path
from typing import Optional

from dm.root_config import get_dataset_root, resolve_dataset_path


def run(args) -> None:
    folder: Optional[str] = getattr(args, "folder", None)
    output: str = args.output

    if folder:
        src_path = resolve_dataset_path(folder)
    else:
        src_path = get_dataset_root()

    if not src_path.exists():
        raise SystemExit(f"Source path not found: {src_path}")

    out_path = Path(output)
    if out_path.exists():
        overwrite = input(f"Output file '{out_path}' already exists. Overwrite? [y/N]: ").strip().lower()
        if overwrite != "y":
            print("Aborted.")
            return

    file_count = 0
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if src_path.is_file():
            zf.write(src_path, src_path.name)
            file_count = 1
        else:
            for file in sorted(src_path.rglob("*")):
                if file.is_file():
                    arcname = file.relative_to(src_path.parent)
                    zf.write(file, arcname)
                    file_count += 1

    print(f"Exported {file_count} file(s) to: {out_path}")
