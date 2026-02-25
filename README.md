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
        "text": "...",
        "..."
    },
    "required_columns": ["text"],
}
```

## Storage

There is a `config.json` in the Dataset Management System's root directory, it specifies two folders:

- `dataset_root`: where the dataset root is stored.
- `recovery`: where the deleted dataset lies.

## Usage

**Create a dataset** 

```
dms create test/d1 
```

First, it will check whether `test/d1` already exists. If so, stop the command and tell the user the dataset already exists.

It will ask the user for:

1. a sample (required)
2. required columns (empty means all row are required)
3. name (optional)
4. description (optional)
5. creator (optional)

After this, the dms will create the folder.

**Add a jsonl file or a folder**

```
dms add test/d1 a.jsonl
dms add test/d1 samples/
```

It will check whether the argument is a file or a folder, then try to add it to the dataset.

For each file to add:

- If it is not a JSONL/CSV file, simply ignore this.
- If it is a CSV file, convert it to JSONL
- A line-by-line check is performed, to ignore the lines not following the given format. (Notice: required properties cannot be an empty string, for example: `{"text": ""}` is not valid if "text" is a required property)
- The commandline will output (1) file is skipped or not; (2) how many entries (lines) are valid / total entries.

In the end, it will show that totally how many samples are added, and how many are inivalid.

**Remove a josnl file from the dataset**

```
dms rm test/d1 a.jsonl
```

Move the file to the `recovery` folder.
It will output the number of entries in the file.

**Rename a dataset**

```
dms mv test/d1 test/d1-new
```

Simply rename the folder name of the dataset

**Update dataset info**

```
dms update test/d1
```

It will ask the users to input the new sample/required columns/name/description/creator information (default remain unchanged)

**Show statistic information**

```
dms stat test
```

Show the statistic information of a given folder, it will output a tree-like view to all the dataset files with number of entries, and average number of chars (with std) in each entry (simply convert it to string)

When the argument is not provided, show the statistic of the whole dataset

**Export dataset**

```
dms export test -o test.zip
```

Export the folder to a zip file.
If the first argument is not provided, export the whole dataset.

**Import dataset**

```
dms import test.zip -o test
```

Unzip the folder and copy the files to the destination folder.  
If there are already the files with the same name, try to compare the files.  
If files are identical, skip it.  
Otherwise, do not import the dataset and output error (data conflict)



