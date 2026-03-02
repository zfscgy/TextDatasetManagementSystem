# Dataset Manager

A command-line tool for managing large-scale text datasets. Datasets are stored as JSONL files inside folders, each with a `config.json` that tracks metadata and operation history.

---

## Table of Contents

- [Dataset Manager](#dataset-manager)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Concepts](#concepts)
    - [Dataset Structure](#dataset-structure)
    - [Dataset Format](#dataset-format)
    - [Root Configuration](#root-configuration)
  - [Commands](#commands)
    - [`init`](#init)
    - [`config`](#config)
    - [`create`](#create)
    - [`add`](#add)
    - [`rm`](#rm)
    - [`mv`](#mv)
    - [`update`](#update)
    - [`stat`](#stat)
    - [`show`](#show)
    - [`prune`](#prune)
    - [`export` / `import`](#export--import)

---

## Installation

Requires **Python 3.10+**. No third-party dependencies.

```bash
pip install -e .
```

The `-e` flag installs in editable mode — changes to the source take effect immediately without reinstalling. This registers the `dms` command system-wide via `pyproject.toml`.

---

## Quick Start

```bash
# 1. Initialize with your dataset root and recovery directories
dms init

# 2. Create a dataset
dms create project/my-dataset

# 3. Add data
dms add project/my-dataset data.jsonl

# 4. Check statistics
dms stat project
```

---

## Concepts

### Dataset Structure

Each dataset is a folder containing:

- One or more `.jsonl` data files
- A `config.json` with metadata:

| Field | Required | Description |
|---|---|---|
| `format` | Yes | Schema definition (sample + required columns) |
| `created_time` | Yes | Creation timestamp |
| `last_modify_time` | Yes | Last modification timestamp |
| `name` | No | Human-readable name |
| `description` | No | Short description |
| `creator` | No | Author |
| `logs` | Auto | Operation history |

Every command that modifies a dataset appends an entry to `logs`:

```json
"logs": [
  "[2026-02-05 10:10:10] dm create test/d1",
  "[2026-02-05 10:10:20] dm add test/d1 sample.jsonl"
]
```

### Dataset Format

The format defines the schema for a dataset using two fields:

- `sample` — a representative example row
- `required_columns` — columns that must be present and non-empty in every entry

**Plain text dataset:**

```json
{
    "sample": { "text": "..." },
    "required_columns": ["text"]
}
```

**Dataset with tags (array of strings):**

```json
{
    "sample": {
        "text": "...",
        "tags": ["tag1"]
    },
    "required_columns": ["text", "tags"]
}
```

Every entry must have a non-empty `tags` array whose items are all strings.

**Multi-turn conversation (array of objects):**

```json
{
    "sample": {
        "turns": [
            {"role": "user", "content": "..."}
        ]
    },
    "required_columns": ["turns"]
}
```

Every entry must have a non-empty `turns` array. Each item must contain at least `role` (string) and `content` (string).

**Array column validation rules:**

- The array must be non-empty.
- Every item must match the type of the first item in the sample array.
- If the sample item is an object, every key defined in the sample must be present in each item with a matching type. Nested objects are checked recursively.

### Root Configuration

The system's `config.json` stores one or more named environment configs. The `active` key selects which one is currently in use:

```json
{
  "active": "default",
  "configs": {
    "default": {
      "dataset_root": "/path/to/datasets",
      "recovery": "/path/to/datasets/.recovery"
    },
    "work": {
      "dataset_root": "/work/datasets",
      "recovery": "/work/datasets/.recovery"
    }
  }
}
```

Each config has two fields:

- `dataset_root` — where datasets are stored
- `recovery` — where removed files are moved (instead of being permanently deleted)

---

## Commands

### `init`

```bash
dms init
```

Interactively sets up the system. You will be prompted for a **dataset root** directory and a **recovery** directory. Both are created automatically and saved as the `"default"` config.

---

### `config`

**Show current configuration:**

```bash
dms config
```

Prints the active config name, `dataset_root`, `recovery` path, and all known config names.

**Add a named configuration:**

```bash
dms config add work
```

Prompts for `dataset_root` and `recovery` and saves them as a new named config. If the name already exists, you will be asked before overwriting.

---

### `create`

```bash
dms create test/d1
```

Creates a new dataset at the given path. Fails if a `config.json` already exists there. You will be prompted for:

1. Sample (required)
2. Required columns — leave empty to require all columns
3. Name (optional)
4. Description (optional)
5. Creator (optional)

---

### `add`

```bash
dms add test/d1 a.jsonl
dms add test/d1 samples/
```

Adds a single file or all files in a directory (searched recursively, processed in sorted order) to a dataset.

**Per-file behavior:**

- Non-JSONL/JSON/CSV files are skipped.
- CSV and JSON files are automatically converted to JSONL.
- Each line is validated against the dataset format — invalid lines are silently dropped.
- Empty required columns (e.g. `{"text": ""}`) are treated as invalid.
- The output shows the number of valid entries out of the total for each file.

**Duplicate filename handling:** If two source files share the same name (e.g. `train/a.jsonl` and `test/a.jsonl`), the second is written as `a_1.jsonl`, the third as `a_2.jsonl`, and so on. This also applies when a file with that name already exists in the dataset.

A summary line at the end shows the total number of entries added.

**Column mapping (`-c`):**

Use `-c SRC:DST` to rename columns before validation. Source and destination use dot notation for nested keys. The flag can be specified multiple times.

```bash
# Rename a top-level column
dms add test/d1 data.jsonl -c old_name:new_name

# Rename a key inside an object column
dms add test/d1 data.jsonl -c meta.lang:meta.language

# Rename a key inside every item of an array column
dms add test/d1 data.jsonl -c messages.from:messages.role

# Multiple mappings at once
dms add test/d1 data.jsonl -c messages.from:messages.role -c messages.value:messages.content
```

Mappings are applied in order before validation, so the renamed columns are what get checked against the dataset format.

---

### `rm`

```bash
dms rm test/d1 a.jsonl
```

Moves a JSONL file to the `recovery` folder instead of deleting it permanently. Outputs the number of entries that were in the file.

---

### `mv`

```bash
dms mv test/d1 test/d1-new
```

Renames a dataset by renaming its folder.

---

### `update`

```bash
dms update test/d1
```

Interactively updates a dataset's metadata (sample, required columns, name, description, creator). Existing values are shown as defaults — press Enter to keep them.

---

### `stat`

```bash
dms stat test
dms stat          # entire dataset root
```

Displays a tree-like overview of all datasets under the given folder. For each JSONL file it shows:

- Number of entries
- Average character length (with standard deviation)

Each dataset includes a `[total]` summary line. A grand total at the end reports the number of datasets and total entries across the whole scope.

---

### `show`

**List datasets:**

```bash
dms show
dms show test
```

Lists all datasets under the given folder (default: entire dataset root). Each line shows the dataset path, its name (if set), and the sample keys from its format. No entry counts are read from disk.

**Show a single dataset's metadata:**

```bash
dms show test/d1
```

When the path points to a specific dataset, displays its full `config.json`:

- Name, description, creator
- Created and last-modified timestamps
- Format: sample keys and required columns
- Full operation log

---

### `prune`

```bash
dms prune test/d1
dms prune -a        # all datasets at once
```

Removes any top-level keys from every JSONL entry that are not defined in the dataset's format sample. Useful for cleaning up extra columns introduced by upstream pipelines. Files are rewritten in-place.

---

### `export` / `import`

**Export to a zip archive:**

```bash
dms export test -o test.zip
dms export -o all.zip       # export entire dataset root
```

**Import from a zip archive:**

```bash
dms import test.zip -o test
```

Unzips and copies files to the destination folder. If a file with the same name already exists:

- **Identical files** — skipped silently.
- **Different files** — import is aborted with a data conflict error.
