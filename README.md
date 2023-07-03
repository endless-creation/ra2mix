# ra2mix
[![PyPI - Version](https://img.shields.io/pypi/v/ra2mix.svg)](https://pypi.org/project/ra2mix)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ra2mix.svg)](https://pypi.org/project/ra2mix)
[![PyPI - License](https://img.shields.io/pypi/l/ra2mix.svg)](https://pypi.org/project/ra2mix)

A python library for working with Red Alert 2 / Yuri's Revenge *.mix files

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
    - [Reading a `*.mix` file](#reading-a-mix-file)
    - [Creating a `*.mix` file](#creating-a-mix-file)

## Installation
```bash
pip install ra2mix
```

## Usage
Import the package

```python
import ra2mix
```

### Reading a `*.mix` file

The `ra2mix.read` function will take a `*.mix` filepath and return a `dict[str, bytes]`
object. The keys are filenames and the values are file data as bytes.

```python
import ra2mix
mix_filepath = "path/to/mixfile.mix"

filemap = ra2mix.read(mix_filepath)
print(f"filenames: {list(filemap.keys())}")

extract_folder = "extract/to/folder"

for filename, file_data in filemap.items():
    print(f"Creating {filename}")
    with open(os.path.join(extract_folder, filename), "wb") as fp:
        fp.write(file_data)
```

---

### Creating a `*.mix` file

The `ra2mix.write` supports three methods for specifying files to include in a new
`*.mix` file:
    - `filemap`: A `dict[str, bytes]` object consisting of filenames and file data
    - `folder_path`: A path to a folder; all files in the folder are added to the mix
    - `filepaths`: A `list[str]` containing exact filepaths to include in the mix

```python
import ra2mix
mix_filepath = "path/to/mixfile.mix"

target_folder = "read/from/folder"

mix_data = ra2mix.write(mix_filepath, folder_path=target_folder)

# Optionally do something with mix_data if you want; file is already written to
# `mix_filepath`
```
