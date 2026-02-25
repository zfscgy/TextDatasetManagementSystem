"""dms import <zip_file> -o <destination> — Import datasets from a zip file."""

import hashlib
import shutil
import zipfile
from pathlib import Path

from dm.root_config import resolve_dataset_path


def _file_hash(path: Path) -> str:
    """Return the SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args) -> None:
    zip_file: str = args.zip_file
    dest_rel: str = args.output

    zip_path = Path(zip_file)
    if not zip_path.exists():
        raise SystemExit(f"Zip file not found: {zip_path}")

    if not zipfile.is_zipfile(zip_path):
        raise SystemExit(f"Not a valid zip file: {zip_path}")

    dest_path = resolve_dataset_path(dest_rel)

    conflicts: list[tuple[Path, str]] = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()

        # First pass: detect conflicts
        for name in names:
            candidate = dest_path / name
            if candidate.exists() and candidate.is_file():
                # Extract to a temp location for comparison
                import tempfile, os
                with tempfile.TemporaryDirectory() as tmpdir:
                    extracted = Path(zf.extract(name, tmpdir))
                    if _file_hash(candidate) != _file_hash(extracted):
                        conflicts.append((candidate, name))

        if conflicts:
            print("ERROR: Data conflict detected. The following files differ:")
            for dest_file, arc_name in conflicts:
                print(f"  {arc_name}  →  {dest_file}")
            raise SystemExit("Import aborted due to data conflicts.")

        # Second pass: extract all, skipping identical files
        skipped = 0
        extracted_count = 0
        for name in names:
            candidate = dest_path / name
            if candidate.exists() and candidate.is_file():
                # Already confirmed identical above
                skipped += 1
                print(f"  [SKIP identical] {name}")
                continue
            candidate.parent.mkdir(parents=True, exist_ok=True)
            zf.extract(name, dest_path)
            extracted_count += 1

    print(f"\nImport complete:")
    print(f"  Extracted : {extracted_count} file(s)")
    print(f"  Skipped   : {skipped} file(s) (identical)")
    print(f"  Destination: {dest_path}")
