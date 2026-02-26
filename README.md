# Dataset Management System

Dataset management for large-scale text datasets. It will store the dataset in JSONL format. Each dataset is a folder, with the JSONL files and a `config.json`. 

`config.json` has the following properties:

- `created_time`
- `last_modify_time`
- `format`
- `name`
- `description`
- `creator`
- `logs`

logs will keep track of all the operations interacted with the dataset like:

```json
"logs": [
        "[2026-02-05 10:10:10] dm create test/d1",
        "[2026-02-05 10:10:20] dm add test/d1 sample.jsonl"
    ]
```

The `created_time`, `last_modify_time`, and `format` are required when creation, and other properties are optional.

This system supports both Linux and Windows.

## Dataset Format

The text dataset format is defined using a JSON with the following properties:

- The `sample` property is a sample of the dataset.
- The `required_columns` property contains the columns that must be present in the sample.

Example:

```json
{
    "sample": {
        "text": "..."
    },
    "required_columns": ["text"]
}
```

**Array of strings** — e.g. a list of tags:

```json
{
    "sample": {
        "text": "...",
        "tags": ["tag1"]
    },
    "required_columns": ["text", "tags"]
}
```

Each entry must have a non-empty `tags` array whose items are all strings.

**Array of objects** — e.g. a multi-turn conversation:

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

Each entry must have a non-empty `turns` array. Every item must be an object containing at least `role` (string) and `content` (string).

Validation rules for array columns:

- A required array column must be non-empty.
- Every item in the array must match the type of the first item in the sample array.
- If the sample item is an object, every key defined in that object must be present in each item with a matching type. Nested objects are checked recursively.

## Installation

Requires Python 3.10+. No third-party dependencies.

**1. Install the `dms` command**

```bash
pip install -e .
```

This registers `dms` as a system-wide command via the `pyproject.toml` entry point. The `-e` flag means edits to the source take effect immediately without reinstalling.

**2. Initialize the system**

```bash
dms init
```

You will be prompted for two directories:

- **Dataset root** — where all datasets are stored.
- **Recovery** — where removed files are moved instead of being permanently deleted.

Both directories are created automatically. The paths are saved under the `"default"` named config in `config.json`.

## Root Configuration

There is a `config.json` in the Dataset Management System's root directory. It holds one or more named configurations, plus an `active` key that selects which one is currently in use:

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

Each named config has two fields:

- `dataset_root`: where datasets are stored.
- `recovery`: where removed files are moved instead of being permanently deleted.

## Usage

**Initialize DMS**
```bash
dms init
```

**Show current configuration**

```bash
dms config
```

Prints the active config name along with its `dataset_root` and `recovery` paths, and the list of all known config names.

**Add a named configuration**

```bash
dms config add work
```

Interactively prompts for `dataset_root` and `recovery` directories and saves them as a new entry (here named `work`) in `config.json`. If the name already exists, it asks before overwriting.

**Create a dataset**

```bash
dms create test/d1
```

Checks whether `test/d1` is already a dataset (contains a `config.json`). If so, the command stops with an error. An existing directory that is not yet a dataset is allowed.

It will ask the user for:

1. a sample (required)
2. required columns (empty means all row are required)
3. name (optional)
4. description (optional)
5. creator (optional)

After this, the dms will create the folder.

**Add a JSONL file or a folder**

```bash
dms add test/d1 a.jsonl
dms add test/d1 samples/
```

Accepts a single file or a directory. When a directory is given it is searched **recursively** — all files in every sub-directory are collected and processed in sorted order.

For each file:

- Non-JSONL/JSON/CSV files are skipped.
- CSV and JSON files are converted to JSONL before being written.
- A line-by-line check is performed; lines that do not match the dataset format are silently dropped. (Note: required columns cannot be an empty string — e.g. `{"text": ""}` is invalid when `text` is required.)
- The output shows whether the file was skipped and how many entries were valid out of the total.

**Duplicate filename handling** — if two source files share the same name (e.g. `train/a.jsonl` and `test/a.jsonl`), the second is written as `a_1.jsonl`, the third as `a_2.jsonl`, and so on. This also applies when a file with that name already exists in the dataset from a previous `dms add`.

At the end a summary line shows how many entries were added in total.

**Column mapping (`-c`)**

Use `-c SRC:DST` to rename columns before validation. The source and destination use dot notation for nested keys. Can be specified multiple times.

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

**Remove a JSONL file from the dataset**

```bash
dms rm test/d1 a.jsonl
```

Move the file to the `recovery` folder.
It will output the number of entries in the file.

**Rename a dataset**

```bash
dms mv test/d1 test/d1-new
```

Simply rename the folder name of the dataset

**Update dataset info**

```bash
dms update test/d1
```

It will ask the users to input the new sample/required columns/name/description/creator information (default remain unchanged)

**Show statistic information**

```bash
dms stat test
```

Shows a tree-like view of all datasets under the given folder. For each JSONL file it prints the number of entries and the average character length (with std). Each dataset also shows a `[total]` summary line aggregating all its files. A grand total line at the end reports the number of datasets and total entries across the whole scope.

When the argument is not provided, show the statistic of the whole dataset root.

**Export dataset**

```bash
dms export test -o test.zip
```

Export the folder to a zip file.
If the first argument is not provided, export the whole dataset.

**Import dataset**

```bash
dms import test.zip -o test
```

Unzip the folder and copy the files to the destination folder.  
If there are already the files with the same name, try to compare the files.  
If files are identical, skip it.  
Otherwise, do not import the dataset and output error (data conflict)

**Prune extra columns from a dataset**

```bash
dms prune test/d1
```

Removes any top-level keys from every JSONL entry that are not defined in the dataset's format sample. Useful for cleaning up files that contain extra columns introduced by upstream pipelines. The files are rewritten in-place.

To prune all datasets at once:

```bash
dms prune -a
```

